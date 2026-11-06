"""Mediciones corporales (RF-06 a RF-11, RN-03 a RN-13, RN-35 a RN-37, RN-70, BD-04)."""

import uuid
from datetime import timedelta

from tests.conftest import hoy_colombia

BASE = "/api/v1/mediciones"


def _url(medicion_id) -> str:
    return f"{BASE}/{medicion_id}"


# --- Registrar ----------------------------------------------------------------
def test_registrar_medicion_calcula_imc_con_la_altura_del_perfil(client, usuario):
    client.put("/api/v1/usuarios/me", headers=usuario.headers, json={"altura_cm": 175})

    resp = client.post(
        BASE,
        headers=usuario.headers,
        json={
            "fecha": f"{hoy_colombia().isoformat()}T07:00:00-05:00",
            "peso_kg": 70,
            "porcentaje_grasa": 18.5,
            "circunf_cintura_cm": 80,
        },
    )

    assert resp.status_code == 201
    cuerpo = resp.json()
    assert cuerpo["usuario_id"] == str(usuario.id)  # RN-60: del token
    assert cuerpo["fecha"] == hoy_colombia().isoformat()
    assert cuerpo["imc"] == 22.9
    assert cuerpo["categoria_imc"] == "normal"
    assert cuerpo["porcentaje_grasa"] == 18.5


def test_sin_altura_el_imc_es_null(client, usuario, crear_medicion):
    cuerpo = crear_medicion(usuario)

    assert cuerpo["imc"] is None
    assert cuerpo["categoria_imc"] is None


def test_una_sola_medicion_por_dia(client, usuario, crear_medicion):
    """BD-04: la segunda del mismo día da 409."""
    crear_medicion(usuario)

    resp = client.post(
        BASE,
        headers=usuario.headers,
        json={"fecha": f"{hoy_colombia().isoformat()}T20:00:00-05:00", "peso_kg": 71},
    )

    assert resp.status_code == 409


def test_otro_usuario_puede_medir_el_mismo_dia(usuario, otro_usuario, crear_medicion):
    crear_medicion(usuario)
    crear_medicion(otro_usuario)  # no choca: la restricción es por usuario


def test_fecha_futura_se_rechaza(client, usuario):
    """RN-70, evaluado en hora de Colombia."""
    manana = hoy_colombia() + timedelta(days=1)
    resp = client.post(
        BASE, headers=usuario.headers, json={"fecha": f"{manana.isoformat()}T08:00:00-05:00", "peso_kg": 70}
    )

    assert resp.status_code == 400
    assert "futura" in resp.json()["detail"]


def test_fecha_sin_zona_horaria_se_interpreta_en_colombia(client, usuario):
    resp = client.post(
        BASE, headers=usuario.headers, json={"fecha": f"{hoy_colombia().isoformat()}T23:30:00", "peso_kg": 70}
    )

    assert resp.status_code == 201
    assert resp.json()["fecha"] == hoy_colombia().isoformat()


def test_fecha_en_utc_cuenta_como_el_dia_de_colombia(client, usuario):
    """H-05: 02:00 UTC del día D es todavía el día D-1 en Bogotá."""
    ayer = hoy_colombia() - timedelta(days=1)
    resp = client.post(
        BASE,
        headers=usuario.headers,
        json={"fecha": f"{hoy_colombia().isoformat()}T02:00:00+00:00", "peso_kg": 70},
    )

    assert resp.status_code == 201
    assert resp.json()["fecha"] == ayer.isoformat()


def test_valores_fuera_de_rango_dan_422(client, usuario):
    fecha = f"{hoy_colombia().isoformat()}T08:00:00-05:00"
    for cuerpo in ({"peso_kg": 0}, {"peso_kg": True}, {"peso_kg": 70, "porcentaje_grasa": 101}):
        resp = client.post(BASE, headers=usuario.headers, json={"fecha": fecha, **cuerpo})
        assert resp.status_code == 422, cuerpo


# --- Historial y detalle ------------------------------------------------------
def test_historial_cronologico_filtrado_y_solo_propio(client, usuario, otro_usuario, crear_medicion):
    hoy = hoy_colombia()
    for dias in (10, 5, 1):
        crear_medicion(usuario, fecha=hoy - timedelta(days=dias), peso_kg=70 + dias)
    crear_medicion(otro_usuario, fecha=hoy - timedelta(days=5))

    todo = client.get(BASE, headers=usuario.headers).json()
    rango = client.get(
        BASE,
        headers=usuario.headers,
        params={"desde": (hoy - timedelta(days=6)).isoformat(), "hasta": (hoy - timedelta(days=1)).isoformat()},
    ).json()

    assert [m["peso_kg"] for m in todo] == [80, 75, 71]
    assert [m["peso_kg"] for m in rango] == [75, 71]


def test_historial_desde_posterior_a_hasta_da_422(client, usuario):
    resp = client.get(BASE, headers=usuario.headers, params={"desde": "2026-02-01", "hasta": "2026-01-01"})

    assert resp.status_code == 422


def test_detalle_propio_y_ajeno(client, usuario, otro_usuario, crear_medicion):
    medicion = crear_medicion(usuario)

    propio = client.get(_url(medicion["id"]), headers=usuario.headers)
    ajeno = client.get(_url(medicion["id"]), headers=otro_usuario.headers)
    inexistente = client.get(_url(uuid.uuid4()), headers=usuario.headers)

    assert propio.status_code == 200
    assert propio.json()["id"] == medicion["id"]
    assert ajeno.status_code == 404  # RN-08: ajeno = inexistente
    assert inexistente.status_code == 404


# --- Editar -------------------------------------------------------------------
def test_editar_es_parcial_y_no_reasigna_dueno(client, usuario, otro_usuario, crear_medicion):
    medicion = crear_medicion(usuario, porcentaje_grasa=20)

    resp = client.put(
        _url(medicion["id"]),
        headers=usuario.headers,
        json={"peso_kg": 68.5, "usuario_id": str(otro_usuario.id)},
    )

    assert resp.status_code == 200
    cuerpo = resp.json()
    assert cuerpo["peso_kg"] == 68.5
    assert cuerpo["porcentaje_grasa"] == 20  # no enviado: no cambia
    assert cuerpo["usuario_id"] == str(usuario.id)  # RN-37


def test_editar_peso_null_no_lo_borra(client, usuario, crear_medicion):
    medicion = crear_medicion(usuario)

    resp = client.put(_url(medicion["id"]), headers=usuario.headers, json={"peso_kg": None})

    assert resp.status_code == 200
    assert resp.json()["peso_kg"] == 70


def test_editar_a_una_fecha_ocupada_da_409(client, usuario, crear_medicion):
    hoy = hoy_colombia()
    crear_medicion(usuario, fecha=hoy)
    otra = crear_medicion(usuario, fecha=hoy - timedelta(days=3))

    resp = client.put(_url(otra["id"]), headers=usuario.headers, json={"fecha": hoy.isoformat()})

    assert resp.status_code == 409


def test_editar_validaciones_y_ajenas(client, usuario, otro_usuario, crear_medicion):
    medicion = crear_medicion(usuario)
    manana = (hoy_colombia() + timedelta(days=1)).isoformat()

    assert client.put(_url(medicion["id"]), headers=usuario.headers, json={"fecha": manana}).status_code == 422
    assert client.put(_url(medicion["id"]), headers=usuario.headers, json={"peso_kg": -1}).status_code == 422
    assert client.put(_url(medicion["id"]), headers=otro_usuario.headers, json={"peso_kg": 60}).status_code == 404


# --- Eliminar -----------------------------------------------------------------
def test_eliminar_medicion(client, usuario, otro_usuario, crear_medicion):
    medicion = crear_medicion(usuario)

    assert client.delete(_url(medicion["id"]), headers=otro_usuario.headers).status_code == 404
    assert client.delete(_url(medicion["id"]), headers=usuario.headers).status_code == 204
    assert client.delete(_url(medicion["id"]), headers=usuario.headers).status_code == 404  # RN-36
    assert client.get(_url(medicion["id"]), headers=usuario.headers).status_code == 404


# --- Inactividad (RF-10) ------------------------------------------------------
def test_inactividad_sin_mediciones(client, usuario):
    resp = client.get(f"{BASE}/inactividad", headers=usuario.headers)

    assert resp.status_code == 200
    assert resp.json() == {"ultima_medicion": None, "dias_desde_ultima_medicion": None, "esta_inactivo": False}


def test_inactividad_umbral_de_30_dias(client, usuario, otro_usuario, crear_medicion):
    hoy = hoy_colombia()
    crear_medicion(usuario, fecha=hoy - timedelta(days=29))
    crear_medicion(otro_usuario, fecha=hoy - timedelta(days=30))

    activo = client.get(f"{BASE}/inactividad", headers=usuario.headers).json()
    inactivo = client.get(f"{BASE}/inactividad", headers=otro_usuario.headers).json()

    assert activo["dias_desde_ultima_medicion"] == 29
    assert activo["esta_inactivo"] is False
    assert inactivo["dias_desde_ultima_medicion"] == 30
    assert inactivo["esta_inactivo"] is True


# --- Comparar (RF-09) ---------------------------------------------------------
def test_comparar_calcula_diferencias_reciente_menos_anterior(client, usuario, crear_medicion):
    client.put("/api/v1/usuarios/me", headers=usuario.headers, json={"altura_cm": 180})
    hoy = hoy_colombia()
    anterior = hoy - timedelta(days=30)
    crear_medicion(usuario, fecha=anterior, peso_kg=80, porcentaje_grasa=25)
    crear_medicion(usuario, fecha=hoy, peso_kg=77.5, porcentaje_grasa=22.3)

    # Se pasan al revés: el orden de los parámetros no importa.
    resp = client.get(
        f"{BASE}/comparar",
        headers=usuario.headers,
        params={"fecha1": hoy.isoformat(), "fecha2": anterior.isoformat()},
    )

    assert resp.status_code == 200
    cuerpo = resp.json()
    assert cuerpo["medicion_anterior"]["fecha"] == anterior.isoformat()
    assert cuerpo["medicion_reciente"]["fecha"] == hoy.isoformat()
    assert cuerpo["diferencias"]["peso_kg"] == -2.5
    assert cuerpo["diferencias"]["porcentaje_grasa"] == -2.7
    assert cuerpo["diferencias"]["imc"] == -0.8  # 23.9 -> 24.7
    assert cuerpo["diferencias"]["masa_muscular_kg"] is None


def test_comparar_errores(client, usuario, crear_medicion):
    hoy = hoy_colombia()
    crear_medicion(usuario, fecha=hoy)
    url = f"{BASE}/comparar"

    misma = client.get(url, headers=usuario.headers, params={"fecha1": hoy.isoformat(), "fecha2": hoy.isoformat()})
    una_falta = client.get(url, headers=usuario.headers, params={"fecha1": hoy.isoformat(), "fecha2": "2025-01-01"})
    ambas = client.get(url, headers=usuario.headers, params={"fecha1": "2025-01-01", "fecha2": "2025-01-02"})

    assert misma.status_code == 400
    assert una_falta.status_code == 404
    assert "2025-01-01" in una_falta.json()["detail"]  # RN-35: dice cuál falta
    assert ambas.status_code == 404
    assert "2025-01-01" in ambas.json()["detail"] and "2025-01-02" in ambas.json()["detail"]
