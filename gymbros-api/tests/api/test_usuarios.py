"""Perfil del usuario autenticado (`/usuarios/me`)."""

ME = "/api/v1/usuarios/me"


def test_obtener_mi_perfil(client, crear_usuario):
    usuario = crear_usuario(correo="Perfil@GymBros-Pruebas.com", nombre="Perfil")

    resp = client.get(ME, headers=usuario.headers)

    assert resp.status_code == 200
    cuerpo = resp.json()
    assert cuerpo["id"] == str(usuario.id)
    assert cuerpo["correo"] == "perfil@gymbros-pruebas.com"
    assert cuerpo["nombre"] == "Perfil"
    assert "hash_password" not in cuerpo  # RN-22: el hash nunca sale


def test_actualizar_mi_perfil_parcialmente(client, usuario):
    resp = client.put(
        ME,
        headers=usuario.headers,
        json={"altura_cm": 175, "sexo": "M", "preferencias_notificacion": {"push": True}},
    )

    assert resp.status_code == 200
    cuerpo = resp.json()
    assert cuerpo["altura_cm"] == 175
    assert cuerpo["preferencias_notificacion"] == {"push": True}
    assert cuerpo["nombre"] == "Usuario de prueba"  # lo omitido no cambia


def test_nombre_null_no_borra_el_nombre(client, usuario):
    resp = client.put(ME, headers=usuario.headers, json={"nombre": None})

    assert resp.status_code == 200
    assert resp.json()["nombre"] == "Usuario de prueba"


def test_actualizar_perfil_invalido_da_422(client, usuario):
    assert client.put(ME, headers=usuario.headers, json={"altura_cm": 10}).status_code == 422
    assert client.put(ME, headers=usuario.headers, json={"nombre": "   "}).status_code == 422


def test_el_correo_no_se_puede_cambiar_por_el_perfil(client, usuario):
    resp = client.put(ME, headers=usuario.headers, json={"correo": "otro@gymbros-pruebas.com"})

    assert resp.status_code == 200
    assert resp.json()["correo"] == usuario.correo


def test_perfil_requiere_autenticacion(client):
    assert client.get(ME).status_code == 401
    assert client.put(ME, json={"nombre": "X"}).status_code == 401
