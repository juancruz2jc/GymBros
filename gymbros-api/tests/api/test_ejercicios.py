"""Catálogo de ejercicios (RF-12, RN-38, RN-39) y último registro (RF-20, RN-50)."""

import uuid

CATALOGO = "/api/v1/ejercicios"


def _ultimo(ejercicio_id) -> str:
    return f"/api/v1/ejercicios/{ejercicio_id}/ultimo-registro"


# --- Catálogo ---------------------------------------------------------------
def test_catalogo_es_publico_y_solo_lista_activos(client, crear_ejercicio):
    activo = crear_ejercicio(nombre_es="Press banca")
    crear_ejercicio(nombre_es="Retirado", activo=False)

    resp = client.get(CATALOGO)  # sin token: RN-38

    assert resp.status_code == 200
    nombres = [e["nombre_es"] for e in resp.json()]
    assert nombres == [activo.nombre_es]
    assert "activo" not in resp.json()[0]


def test_catalogo_filtra_y_normaliza(client, crear_ejercicio):
    crear_ejercicio(nombre_es="Sentadilla", grupo_muscular="piernas", equipo="barra")
    crear_ejercicio(nombre_es="Zancada", grupo_muscular="piernas", equipo="mancuerna")
    crear_ejercicio(nombre_es="Remo", grupo_muscular="espalda", equipo="barra")

    piernas = client.get(CATALOGO, params={"grupo_muscular": " Piernas "}).json()
    piernas_barra = client.get(CATALOGO, params={"grupo_muscular": "piernas", "equipo": "barra"}).json()
    vacio_es_sin_filtro = client.get(CATALOGO, params={"grupo_muscular": ""}).json()  # GYM-179
    categoria = client.get(CATALOGO, params={"categoria": "cardio"}).json()

    assert [e["nombre_es"] for e in piernas] == ["Sentadilla", "Zancada"]
    assert [e["nombre_es"] for e in piernas_barra] == ["Sentadilla"]
    assert len(vacio_es_sin_filtro) == 3
    assert categoria == []


def test_catalogo_ordena_por_grupo_y_nombre(client, crear_ejercicio):
    crear_ejercicio(nombre_es="B", grupo_muscular="pecho")
    crear_ejercicio(nombre_es="A", grupo_muscular="pecho")
    crear_ejercicio(nombre_es="Z", grupo_muscular="espalda")

    nombres = [e["nombre_es"] for e in client.get(CATALOGO).json()]

    assert nombres == ["Z", "A", "B"]


def test_catalogo_es_de_solo_lectura(client, usuario):
    """RN-38: no hay alta de ejercicios para el usuario final."""
    resp = client.post(CATALOGO, headers=usuario.headers, json={"nombre_es": "X"})

    assert resp.status_code == 405


# --- Último registro --------------------------------------------------------
def test_ultimo_registro_sin_historial_es_null(client, usuario, ejercicio):
    resp = client.get(_ultimo(ejercicio.id), headers=usuario.headers)

    assert resp.status_code == 200
    assert resp.json() is None


def test_ultimo_registro_toma_la_sesion_mas_reciente_y_la_ultima_serie(
    client, usuario, ejercicio, sesion_finalizada
):
    sesion_finalizada(
        usuario,
        [(ejercicio, 1, 10, 40.0), (ejercicio, 2, 8, 45.0)],
        iniciada_en="2026-01-05T10:00:00-05:00",
        finalizada_en="2026-01-05T11:00:00-05:00",
    )
    reciente = sesion_finalizada(
        usuario,
        [(ejercicio, 1, 10, 50.0), (ejercicio, 2, 6, 55.0)],
        iniciada_en="2026-01-12T10:00:00-05:00",
        finalizada_en="2026-01-12T11:00:00-05:00",
    )

    resp = client.get(_ultimo(ejercicio.id), headers=usuario.headers)

    assert resp.status_code == 200
    cuerpo = resp.json()
    assert cuerpo["sesion_id"] == reciente["id"]
    assert cuerpo["numero_serie"] == 2
    assert cuerpo["repeticiones_realizadas"] == 6
    assert cuerpo["peso_usado_kg"] == 55.0


def test_ultimo_registro_ignora_sesion_activa_y_sesiones_ajenas(
    client, usuario, otro_usuario, ejercicio, sesion_finalizada, iniciar_sesion, registrar_series
):
    sesion_finalizada(otro_usuario, [(ejercicio, 1, 10, 100.0)])
    activa = iniciar_sesion(usuario)
    registrar_series(
        usuario,
        activa["id"],
        [{"ejercicio_id": str(ejercicio.id), "numero_serie": 1, "repeticiones_realizadas": 5,
          "peso_usado_kg": 20, "orden": 1}],
    )

    resp = client.get(_ultimo(ejercicio.id), headers=usuario.headers)

    assert resp.json() is None


def test_ultimo_registro_de_ejercicio_desactivado_sigue_disponible(
    client, db, usuario, ejercicio, sesion_finalizada
):
    """RN-39: un ejercicio desactivado conserva su historial."""
    sesion_finalizada(usuario, [(ejercicio, 1, 10, 30.0)])
    ejercicio.activo = False
    db.commit()

    resp = client.get(_ultimo(ejercicio.id), headers=usuario.headers)

    assert resp.status_code == 200
    assert resp.json()["peso_usado_kg"] == 30.0


def test_ultimo_registro_errores(client, usuario):
    assert client.get(_ultimo(uuid.uuid4()), headers=usuario.headers).status_code == 404
    assert client.get(_ultimo("no-uuid"), headers=usuario.headers).status_code == 422
    assert client.get(_ultimo(uuid.uuid4())).status_code == 401
