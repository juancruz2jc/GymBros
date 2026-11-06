"""Rutinas propias (RF-13, RF-14, RF-21, RF-22, RN-39, RN-43, RN-60, RN-64)."""

import uuid

BASE = "/api/v1/rutinas"


def _url(rutina_id, sufijo: str = "") -> str:
    return f"{BASE}/{rutina_id}{sufijo}"


def _ejercicio_en_rutina(ejercicio, orden: int = 1) -> dict:
    return {
        "ejercicio_id": str(ejercicio.id),
        "orden": orden,
        "series_objetivo": 4,
        "repeticiones_objetivo": 8,
        "descanso_segundos": 120,
    }


# --- Crear ------------------------------------------------------------------
def test_crear_rutina_con_ejercicios(client, usuario, crear_ejercicio):
    a, b = crear_ejercicio(), crear_ejercicio()

    resp = client.post(
        BASE,
        headers=usuario.headers,
        json={
            "nombre": "Torso",
            "favorita": True,
            "ejercicios": [_ejercicio_en_rutina(a, 1), _ejercicio_en_rutina(b, 2)],
        },
    )

    assert resp.status_code == 201
    cuerpo = resp.json()
    assert cuerpo["usuario_id"] == str(usuario.id)
    assert cuerpo["nombre"] == "Torso"
    assert cuerpo["favorita"] is True
    assert sorted(e["orden"] for e in cuerpo["ejercicios"]) == [1, 2]


def test_crear_rutina_validaciones_de_negocio(client, usuario, crear_ejercicio):
    activo = crear_ejercicio()
    inactivo = crear_ejercicio(activo=False)

    def crear(ejercicios):
        return client.post(BASE, headers=usuario.headers, json={"nombre": "X", "ejercicios": ejercicios})

    orden_repetido = crear([_ejercicio_en_rutina(activo, 1), _ejercicio_en_rutina(activo, 1)])
    inexistente = crear([{**_ejercicio_en_rutina(activo), "ejercicio_id": str(uuid.uuid4())}])
    con_inactivo = crear([_ejercicio_en_rutina(inactivo)])
    sin_ejercicios = crear([])

    assert orden_repetido.status_code == 422
    assert "orden" in orden_repetido.json()["detail"]
    assert inexistente.status_code == 422
    assert con_inactivo.status_code == 422
    assert "inactivo" in con_inactivo.json()["detail"]
    assert sin_ejercicios.status_code == 422


def test_rutinas_requieren_autenticacion(client):
    assert client.get(BASE).status_code == 401
    assert client.post(BASE, json={}).status_code == 401


# --- Listar y obtener -------------------------------------------------------
def test_listar_solo_las_propias_y_filtrar_favoritas(
    client, usuario, otro_usuario, ejercicio, crear_rutina
):
    crear_rutina(usuario, [ejercicio], nombre="Normal")
    fav = crear_rutina(usuario, [ejercicio], nombre="Fav", favorita=True)
    crear_rutina(otro_usuario, [ejercicio], nombre="Ajena")

    todas = client.get(BASE, headers=usuario.headers).json()
    favoritas = client.get(BASE, headers=usuario.headers, params={"favoritas": "true"}).json()

    assert sorted(r["nombre"] for r in todas) == ["Fav", "Normal"]
    assert [r["id"] for r in favoritas] == [fav["id"]]


def test_obtener_rutina_propia_ajena_e_inexistente(client, usuario, otro_usuario, ejercicio, crear_rutina):
    rutina = crear_rutina(usuario, [ejercicio])

    assert client.get(_url(rutina["id"]), headers=usuario.headers).status_code == 200
    assert client.get(_url(rutina["id"]), headers=otro_usuario.headers).status_code == 404
    assert client.get(_url(uuid.uuid4()), headers=usuario.headers).status_code == 404


# --- Actualizar -------------------------------------------------------------
def test_actualizar_nombre_sin_tocar_ejercicios(client, usuario, ejercicio, crear_rutina):
    rutina = crear_rutina(usuario, [ejercicio])

    resp = client.put(_url(rutina["id"]), headers=usuario.headers, json={"nombre": "Renombrada", "favorita": True})

    assert resp.status_code == 200
    cuerpo = resp.json()
    assert cuerpo["nombre"] == "Renombrada"
    assert cuerpo["favorita"] is True
    assert len(cuerpo["ejercicios"]) == 1


def test_actualizar_reemplaza_la_lista_de_ejercicios(client, usuario, crear_ejercicio, crear_rutina):
    a, b, c = crear_ejercicio(), crear_ejercicio(), crear_ejercicio()
    rutina = crear_rutina(usuario, [a, b])

    resp = client.put(
        _url(rutina["id"]), headers=usuario.headers, json={"ejercicios": [_ejercicio_en_rutina(c)]}
    )

    assert resp.status_code == 200
    assert [e["ejercicio_id"] for e in resp.json()["ejercicios"]] == [str(c.id)]


def test_actualizar_valida_y_protege_ajenas(client, usuario, otro_usuario, crear_ejercicio, crear_rutina):
    ej = crear_ejercicio()
    inactivo = crear_ejercicio(activo=False)
    rutina = crear_rutina(usuario, [ej])

    con_inactivo = client.put(
        _url(rutina["id"]), headers=usuario.headers, json={"ejercicios": [_ejercicio_en_rutina(inactivo)]}
    )
    ajena = client.put(_url(rutina["id"]), headers=otro_usuario.headers, json={"nombre": "Robada"})

    assert con_inactivo.status_code == 422
    assert ajena.status_code == 404
    assert client.get(_url(rutina["id"]), headers=usuario.headers).json()["nombre"] == "Rutina de prueba"


# --- Favorita (RF-22) -------------------------------------------------------
def test_alternar_favorita(client, usuario, otro_usuario, ejercicio, crear_rutina):
    rutina = crear_rutina(usuario, [ejercicio])
    url = _url(rutina["id"], "/favorita")

    assert client.patch(url, headers=usuario.headers).json()["favorita"] is True
    assert client.patch(url, headers=usuario.headers).json()["favorita"] is False
    assert client.patch(url, headers=otro_usuario.headers).status_code == 404
    assert client.patch(_url(uuid.uuid4(), "/favorita"), headers=usuario.headers).status_code == 404


def test_rutina_con_ejercicio_desactivado_se_puede_marcar_favorita(client, db, usuario, ejercicio, crear_rutina):
    """RN-39: la rutina sigue siendo válida."""
    rutina = crear_rutina(usuario, [ejercicio])
    ejercicio.activo = False
    db.commit()

    resp = client.patch(_url(rutina["id"], "/favorita"), headers=usuario.headers)

    assert resp.status_code == 200
    assert resp.json()["favorita"] is True


# --- Duplicar (RF-21) -------------------------------------------------------
def test_duplicar_rutina(client, usuario, otro_usuario, crear_ejercicio, crear_rutina):
    rutina = crear_rutina(usuario, [crear_ejercicio(), crear_ejercicio()], nombre="Pierna", favorita=True)

    resp = client.post(_url(rutina["id"], "/duplicar"), headers=usuario.headers)

    assert resp.status_code == 201
    copia = resp.json()
    assert copia["id"] != rutina["id"]
    assert copia["nombre"] == "Pierna (copia)"
    assert copia["favorita"] is False
    assert sorted(e["ejercicio_id"] for e in copia["ejercicios"]) == sorted(
        e["ejercicio_id"] for e in rutina["ejercicios"]
    )
    assert client.post(_url(rutina["id"], "/duplicar"), headers=otro_usuario.headers).status_code == 404


# --- Eliminar (RF-14) -------------------------------------------------------
def test_eliminar_rutina(client, usuario, otro_usuario, ejercicio, crear_rutina):
    rutina = crear_rutina(usuario, [ejercicio])

    assert client.delete(_url(rutina["id"]), headers=otro_usuario.headers).status_code == 404
    assert client.delete(_url(rutina["id"]), headers=usuario.headers).status_code == 204
    assert client.get(_url(rutina["id"]), headers=usuario.headers).status_code == 404
    assert client.delete(_url(rutina["id"]), headers=usuario.headers).status_code == 404


def test_eliminar_rutina_conserva_las_sesiones_como_entrenamiento_libre(
    client, usuario, ejercicio, crear_rutina, sesion_finalizada
):
    """RN-43: la sesión queda en el historial con rutina_id = null."""
    rutina = crear_rutina(usuario, [ejercicio], nombre="Se borrará")
    sesion = sesion_finalizada(usuario, [(ejercicio, 1, 10, 50.0)], rutina_id=rutina["id"])

    assert client.delete(_url(rutina["id"]), headers=usuario.headers).status_code == 204

    detalle = client.get(f"/api/v1/sesiones/{sesion['id']}", headers=usuario.headers).json()
    assert detalle["rutina_id"] is None
    assert detalle["rutina_nombre"] == "Entrenamiento libre"
