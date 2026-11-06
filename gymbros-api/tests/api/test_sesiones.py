"""Sesiones de entrenamiento y series (RF-15 a RF-19, RN-43 a RN-49, RN-60, RN-67 a RN-69)."""

import uuid
from datetime import datetime, timedelta, timezone

BASE = "/api/v1/sesiones"


def _url(sesion_id, sufijo: str = "") -> str:
    return f"{BASE}/{sesion_id}{sufijo}"


def _serie(ejercicio, numero: int = 1, reps: int = 10, peso: float = 50, orden: int = 1) -> dict:
    return {
        "ejercicio_id": str(ejercicio.id),
        "numero_serie": numero,
        "repeticiones_realizadas": reps,
        "peso_usado_kg": peso,
        "orden": orden,
    }


# --- Iniciar (RF-15) ----------------------------------------------------------
def test_iniciar_sesion_libre(client, usuario):
    resp = client.post(BASE, headers=usuario.headers, json={"idempotency_key": "clave-1"})

    assert resp.status_code == 201
    cuerpo = resp.json()
    assert cuerpo["rutina_id"] is None
    assert cuerpo["finalizada_en"] is None
    assert cuerpo["idempotency_key"] == "clave-1"


def test_iniciar_desde_rutina_propia_y_ajena(client, usuario, otro_usuario, ejercicio, crear_rutina):
    propia = crear_rutina(usuario, [ejercicio])
    ajena = crear_rutina(otro_usuario, [ejercicio])

    con_ajena = client.post(BASE, headers=usuario.headers, json={"idempotency_key": "a", "rutina_id": ajena["id"]})
    con_propia = client.post(BASE, headers=usuario.headers, json={"idempotency_key": "b", "rutina_id": propia["id"]})

    assert con_ajena.status_code == 404  # RN-60
    assert con_propia.status_code == 201
    assert con_propia.json()["rutina_id"] == propia["id"]


def test_reintento_con_la_misma_clave_no_duplica(client, usuario):
    """RN-67: idempotencia para reintentos sin conexión."""
    primera = client.post(BASE, headers=usuario.headers, json={"idempotency_key": "offline-1"})
    reintento = client.post(BASE, headers=usuario.headers, json={"idempotency_key": "offline-1"})

    assert primera.status_code == 201
    assert reintento.status_code == 200
    assert reintento.json()["id"] == primera.json()["id"]


def test_clave_de_otra_cuenta_da_409(client, usuario, otro_usuario):
    client.post(BASE, headers=usuario.headers, json={"idempotency_key": "compartida"})

    resp = client.post(BASE, headers=otro_usuario.headers, json={"idempotency_key": "compartida"})

    assert resp.status_code == 409


def test_solo_una_sesion_activa(client, usuario, iniciar_sesion):
    """RN-44."""
    activa = iniciar_sesion(usuario)

    resp = client.post(BASE, headers=usuario.headers, json={"idempotency_key": "otra"})

    assert resp.status_code == 409
    assert activa["id"] in resp.json()["detail"]


def test_inicio_futuro_se_rechaza_con_tolerancia_de_reloj(client, usuario):
    ahora = datetime.now(timezone.utc)
    futuro = (ahora + timedelta(minutes=30)).isoformat()
    casi_ahora = (ahora + timedelta(minutes=2)).isoformat()

    rechazada = client.post(BASE, headers=usuario.headers, json={"idempotency_key": "f", "iniciada_en": futuro})
    aceptada = client.post(BASE, headers=usuario.headers, json={"idempotency_key": "g", "iniciada_en": casi_ahora})

    assert rechazada.status_code == 422
    assert aceptada.status_code == 201


# --- Activa (RN-68) -----------------------------------------------------------
def test_sesion_activa(client, usuario, iniciar_sesion):
    assert client.get(f"{BASE}/activa", headers=usuario.headers).status_code == 404

    activa = iniciar_sesion(usuario)
    resp = client.get(f"{BASE}/activa", headers=usuario.headers)

    assert resp.status_code == 200
    assert resp.json()["id"] == activa["id"]


# --- Series (RF-16) -----------------------------------------------------------
def test_registrar_una_serie_o_un_lote(client, usuario, crear_ejercicio, iniciar_sesion):
    a, b = crear_ejercicio(), crear_ejercicio()
    sesion = iniciar_sesion(usuario)

    una = client.post(_url(sesion["id"], "/series"), headers=usuario.headers, json={"series": _serie(a)})
    lote = client.post(
        _url(sesion["id"], "/series"),
        headers=usuario.headers,
        json={"series": [_serie(a, numero=2, orden=2), _serie(b, numero=1, orden=3, peso=0, reps=0)]},
    )

    assert una.status_code == 201
    assert len(una.json()) == 1
    assert lote.status_code == 201
    assert [s["numero_serie"] for s in lote.json()] == [2, 1]


def test_registrar_la_misma_serie_la_actualiza(client, usuario, ejercicio, iniciar_sesion):
    """BD-04: upsert por (sesión, ejercicio, número de serie)."""
    sesion = iniciar_sesion(usuario)
    url = _url(sesion["id"], "/series")

    primera = client.post(url, headers=usuario.headers, json={"series": _serie(ejercicio, reps=10, peso=40)}).json()
    segunda = client.post(url, headers=usuario.headers, json={"series": _serie(ejercicio, reps=12, peso=42.5)}).json()

    assert segunda[0]["id"] == primera[0]["id"]
    assert segunda[0]["repeticiones_realizadas"] == 12
    assert segunda[0]["peso_usado_kg"] == 42.5


def test_series_errores(client, usuario, otro_usuario, ejercicio, iniciar_sesion, sesion_finalizada):
    activa = iniciar_sesion(usuario)
    url = _url(activa["id"], "/series")

    ajena = client.post(url, headers=otro_usuario.headers, json={"series": _serie(ejercicio)})
    inexistente = client.post(_url(uuid.uuid4(), "/series"), headers=usuario.headers, json={"series": _serie(ejercicio)})
    ejercicio_falso = client.post(
        url, headers=usuario.headers, json={"series": {**_serie(ejercicio), "ejercicio_id": str(uuid.uuid4())}}
    )
    repetida = client.post(url, headers=usuario.headers, json={"series": [_serie(ejercicio), _serie(ejercicio)]})
    booleano = client.post(url, headers=usuario.headers, json={"series": {**_serie(ejercicio), "peso_usado_kg": True}})

    assert ajena.status_code == 404
    assert inexistente.status_code == 404
    assert ejercicio_falso.status_code == 404
    assert repetida.status_code == 422
    assert booleano.status_code == 422


def test_no_se_registran_series_en_sesion_finalizada(client, usuario, ejercicio, sesion_finalizada):
    sesion = sesion_finalizada(usuario, [(ejercicio, 1, 10, 50.0)])

    resp = client.post(_url(sesion["id"], "/series"), headers=usuario.headers, json={"series": _serie(ejercicio, 2)})

    assert resp.status_code == 409


def test_ejercicio_desactivado_sigue_valido_en_sesiones(client, db, usuario, ejercicio, iniciar_sesion):
    """RN-39."""
    ejercicio.activo = False
    db.commit()
    sesion = iniciar_sesion(usuario)

    resp = client.post(_url(sesion["id"], "/series"), headers=usuario.headers, json={"series": _serie(ejercicio)})

    assert resp.status_code == 201


# --- Finalizar (RF-17) --------------------------------------------------------
def test_finalizar_calcula_la_duracion(client, usuario, ejercicio, iniciar_sesion, registrar_series):
    """RN-47."""
    sesion = iniciar_sesion(usuario, iniciada_en="2026-01-10T10:00:00-05:00")
    registrar_series(usuario, sesion["id"], [_serie(ejercicio)])

    resp = client.post(
        _url(sesion["id"], "/finalizar"),
        headers=usuario.headers,
        json={"finalizada_en": "2026-01-10T11:15:30-05:00"},
    )

    assert resp.status_code == 200
    assert resp.json()["duracion_segundos"] == 75 * 60 + 30
    assert client.get(f"{BASE}/activa", headers=usuario.headers).status_code == 404


def test_finalizar_sin_body_usa_la_hora_del_servidor(client, usuario, ejercicio, iniciar_sesion, registrar_series):
    sesion = iniciar_sesion(usuario)
    registrar_series(usuario, sesion["id"], [_serie(ejercicio)])

    resp = client.post(_url(sesion["id"], "/finalizar"), headers=usuario.headers)

    assert resp.status_code == 200
    assert resp.json()["finalizada_en"] is not None


def test_finalizar_sin_series_exige_confirmacion(client, usuario, iniciar_sesion):
    """RN-69."""
    sesion = iniciar_sesion(usuario)
    url = _url(sesion["id"], "/finalizar")

    sin_confirmar = client.post(url, headers=usuario.headers, json={})
    confirmada = client.post(url, headers=usuario.headers, json={"confirmar_sin_series": True})

    assert sin_confirmar.status_code == 409
    assert "confirmar_sin_series" in sin_confirmar.json()["detail"]
    assert confirmada.status_code == 200


def test_finalizar_errores(client, usuario, otro_usuario, iniciar_sesion, sesion_finalizada):
    activa = iniciar_sesion(usuario, iniciada_en="2026-01-10T10:00:00-05:00")
    url = _url(activa["id"], "/finalizar")
    confirmar = {"confirmar_sin_series": True}
    futura = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()

    ajena = client.post(url, headers=otro_usuario.headers, json=confirmar)
    antes_del_inicio = client.post(
        url, headers=usuario.headers, json={**confirmar, "finalizada_en": "2026-01-10T09:00:00-05:00"}
    )
    en_el_futuro = client.post(url, headers=usuario.headers, json={**confirmar, "finalizada_en": futura})
    ok = client.post(url, headers=usuario.headers, json=confirmar)
    dos_veces = client.post(url, headers=usuario.headers, json=confirmar)

    assert ajena.status_code == 404
    assert antes_del_inicio.status_code == 422
    assert en_el_futuro.status_code == 422
    assert ok.status_code == 200
    assert dos_veces.status_code == 409  # RN-47


# --- Descartar (RN-68) --------------------------------------------------------
def test_descartar_sesion_activa_borra_sus_series(client, usuario, ejercicio, iniciar_sesion, registrar_series):
    sesion = iniciar_sesion(usuario)
    registrar_series(usuario, sesion["id"], [_serie(ejercicio)])

    resp = client.delete(_url(sesion["id"]), headers=usuario.headers)

    assert resp.status_code == 204
    assert client.get(f"{BASE}/activa", headers=usuario.headers).status_code == 404
    # Se puede iniciar otra: ya no hay sesión activa (RN-44).
    assert client.post(BASE, headers=usuario.headers, json={"idempotency_key": "nueva"}).status_code == 201
    # Las series se fueron en cascada: no hay "último registro".
    assert client.get(f"/api/v1/ejercicios/{ejercicio.id}/ultimo-registro", headers=usuario.headers).json() is None


def test_descartar_errores(client, usuario, otro_usuario, iniciar_sesion, sesion_finalizada):
    finalizada = sesion_finalizada(usuario, [])
    activa = iniciar_sesion(usuario)

    assert client.delete(_url(finalizada["id"]), headers=usuario.headers).status_code == 409
    assert client.delete(_url(activa["id"]), headers=otro_usuario.headers).status_code == 404
    assert client.delete(_url(uuid.uuid4()), headers=usuario.headers).status_code == 404


# --- Calificar (RF-18) --------------------------------------------------------
def test_calificar_y_corregir_calificacion(client, usuario, sesion_finalizada):
    sesion = sesion_finalizada(usuario, [])
    url = _url(sesion["id"], "/calificacion")

    primera = client.patch(url, headers=usuario.headers, json={"calificacion": 4, "nota": "Bien"})
    corregida = client.patch(url, headers=usuario.headers, json={"calificacion": 5})

    assert primera.status_code == 200
    assert primera.json()["calificacion"] == 4
    assert primera.json()["nota"] == "Bien"
    assert corregida.json()["calificacion"] == 5


def test_calificar_errores(client, usuario, otro_usuario, iniciar_sesion, sesion_finalizada):
    finalizada = sesion_finalizada(usuario, [])
    activa = iniciar_sesion(usuario)

    def calificar(sesion_id, cuerpo, quien=usuario):
        return client.patch(_url(sesion_id, "/calificacion"), headers=quien.headers, json=cuerpo)

    assert calificar(activa["id"], {"calificacion": 3}).status_code == 409
    assert calificar(finalizada["id"], {"calificacion": 3}, quien=otro_usuario).status_code == 404
    assert calificar(uuid.uuid4(), {"calificacion": 3}).status_code == 404
    assert calificar(finalizada["id"], {"calificacion": 6}).status_code == 422
    assert calificar(finalizada["id"], {"calificacion": True}).status_code == 422


# --- Historial (RF-19) --------------------------------------------------------
def test_historial_solo_finalizadas_propias_y_mas_recientes_primero(
    client, usuario, otro_usuario, ejercicio, crear_rutina, iniciar_sesion, sesion_finalizada
):
    rutina = crear_rutina(usuario, [ejercicio], nombre="Empuje")
    vieja = sesion_finalizada(
        usuario, [], iniciada_en="2026-01-01T10:00:00-05:00", finalizada_en="2026-01-01T11:00:00-05:00"
    )
    nueva = sesion_finalizada(
        usuario,
        [],
        iniciada_en="2026-01-03T10:00:00-05:00",
        finalizada_en="2026-01-03T11:00:00-05:00",
        rutina_id=rutina["id"],
    )
    sesion_finalizada(otro_usuario, [])
    iniciar_sesion(usuario)  # activa: no aparece en el historial

    resp = client.get(BASE, headers=usuario.headers)

    assert resp.status_code == 200
    items = resp.json()
    assert [s["id"] for s in items] == [nueva["id"], vieja["id"]]  # RN-49
    assert items[0]["rutina_nombre"] == "Empuje"
    assert items[1]["rutina_nombre"] == "Entrenamiento libre"
    assert items[0]["duracion_segundos"] == 3600


def test_historial_paginado_y_filtrado_por_dia_de_bogota(client, usuario, sesion_finalizada):
    for dia in (1, 2, 3):
        sesion_finalizada(
            usuario,
            [],
            iniciada_en=f"2026-01-0{dia}T10:00:00-05:00",
            finalizada_en=f"2026-01-0{dia}T11:00:00-05:00",
        )
    # 23:30 en Bogotá del día 3 = 04:30 UTC del día 4: debe contar como día 3.
    tarde = sesion_finalizada(
        usuario, [], iniciada_en="2026-01-04T04:30:00+00:00", finalizada_en="2026-01-04T05:00:00+00:00"
    )

    pagina1 = client.get(BASE, headers=usuario.headers, params={"limit": 2}).json()
    pagina2 = client.get(BASE, headers=usuario.headers, params={"limit": 2, "offset": 2}).json()
    dia3 = client.get(BASE, headers=usuario.headers, params={"desde": "2026-01-03", "hasta": "2026-01-03"}).json()

    assert len(pagina1) == 2 and len(pagina2) == 2
    assert not {s["id"] for s in pagina1} & {s["id"] for s in pagina2}
    assert len(dia3) == 2
    assert tarde["id"] in {s["id"] for s in dia3}


def test_historial_parametros_invalidos(client, usuario):
    for params in ({"limit": 0}, {"limit": 101}, {"offset": -1}, {"desde": "2026-02-01", "hasta": "2026-01-01"}):
        assert client.get(BASE, headers=usuario.headers, params=params).status_code == 422, params


def test_detalle_agrupa_series_por_ejercicio(client, usuario, crear_ejercicio, sesion_finalizada):
    a = crear_ejercicio(nombre_es="Press", nombre_en="Press")
    b = crear_ejercicio(nombre_es="Fondos", nombre_en="Dips")
    sesion = sesion_finalizada(usuario, [(a, 1, 10, 60.0), (a, 2, 8, 65.0), (b, 1, 12, 0.0)])
    client.patch(_url(sesion["id"], "/calificacion"), headers=usuario.headers, json={"calificacion": 4, "nota": "Ok"})

    resp = client.get(_url(sesion["id"]), headers=usuario.headers)

    assert resp.status_code == 200
    cuerpo = resp.json()
    assert cuerpo["nota"] == "Ok"
    assert cuerpo["calificacion"] == 4
    assert [e["nombre_es"] for e in cuerpo["ejercicios"]] == ["Press", "Fondos"]
    assert [s["numero_serie"] for s in cuerpo["ejercicios"][0]["series"]] == [1, 2]
    assert cuerpo["ejercicios"][1]["series"][0]["peso_usado_kg"] == 0.0


def test_detalle_errores(client, usuario, otro_usuario, iniciar_sesion, sesion_finalizada):
    finalizada = sesion_finalizada(usuario, [])
    activa = iniciar_sesion(usuario)

    assert client.get(_url(finalizada["id"]), headers=otro_usuario.headers).status_code == 404  # RN-60
    assert client.get(_url(activa["id"]), headers=usuario.headers).status_code == 404  # activa: va en /activa
    assert client.get(_url(uuid.uuid4()), headers=usuario.headers).status_code == 404
    assert client.get(_url("no-uuid"), headers=usuario.headers).status_code == 422
