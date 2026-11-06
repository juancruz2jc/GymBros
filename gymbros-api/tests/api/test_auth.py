"""Autenticación: registro, login, logout y refresh (RF-01, RF-02, RN-20 a RN-26)."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.security import hashear_token
from app.models.usuario import RefreshToken, Usuario
from tests.conftest import PASSWORD_PRUEBA

REGISTRO = "/api/v1/auth/registro"
LOGIN = "/api/v1/auth/login"
LOGOUT = "/api/v1/auth/logout"
REFRESH = "/api/v1/auth/refresh"


def _datos_registro(**campos):
    datos = {
        "correo": "Nuevo.Usuario@GymBros-Pruebas.com",
        "password": "Clave12345",
        "nombre": "Nuevo",
        "consentimiento_datos": True,
    }
    datos.update(campos)
    return datos


# --- Registro ---------------------------------------------------------------
def test_registro_crea_usuario_y_deja_sesion_iniciada(client, db):
    resp = client.post(REGISTRO, json=_datos_registro())

    assert resp.status_code == 201
    cuerpo = resp.json()
    assert cuerpo["token_type"] == "bearer"
    assert cuerpo["access_token"] and cuerpo["refresh_token"]
    assert cuerpo["expires_in"] == 15 * 60

    usuario = db.execute(select(Usuario)).scalar_one()
    assert usuario.correo == "nuevo.usuario@gymbros-pruebas.com"  # RN-20: normalizado
    assert usuario.hash_password != "Clave12345"  # RN-22
    assert usuario.consentimiento_datos is True
    assert usuario.consentimiento_en is not None


def test_registro_con_correo_repetido_da_409_sin_importar_mayusculas(client):
    assert client.post(REGISTRO, json=_datos_registro()).status_code == 201

    resp = client.post(REGISTRO, json=_datos_registro(correo="NUEVO.usuario@gymbros-pruebas.com"))

    assert resp.status_code == 409
    assert "ya está registrado" in resp.json()["detail"]


def test_registro_invalido_no_devuelve_la_password_en_el_error(client):
    """RN-22: el 422 no debe hacer eco de la contraseña."""
    resp = client.post(REGISTRO, json=_datos_registro(password="debil"))

    assert resp.status_code == 422
    assert "debil" not in resp.text
    assert all("input" not in err for err in resp.json()["detail"])


def test_registro_sin_consentimiento_da_422(client):
    resp = client.post(REGISTRO, json=_datos_registro(consentimiento_datos=False))

    assert resp.status_code == 422


# --- Login ------------------------------------------------------------------
def test_login_correcto(client, usuario):
    resp = client.post(LOGIN, json={"correo": usuario.correo.upper(), "password": PASSWORD_PRUEBA})

    assert resp.status_code == 200
    assert resp.json()["access_token"]


def test_login_con_password_incorrecta_o_correo_inexistente_da_el_mismo_401(client, usuario):
    """RN-24: el error no revela si el correo existe."""
    mala_clave = client.post(LOGIN, json={"correo": usuario.correo, "password": "Incorrecta1"})
    sin_cuenta = client.post(
        LOGIN, json={"correo": "nadie@gymbros-pruebas.com", "password": "Incorrecta1"}
    )

    assert mala_clave.status_code == sin_cuenta.status_code == 401
    assert mala_clave.json() == sin_cuenta.json()


# --- Refresh (rotación) -----------------------------------------------------
def test_refresh_emite_par_nuevo_y_revoca_el_anterior(client, usuario):
    resp = client.post(REFRESH, json={"refresh_token": usuario.refresh_token})

    assert resp.status_code == 200
    nuevo = resp.json()
    assert nuevo["refresh_token"] != usuario.refresh_token

    # El viejo ya no sirve (defensa contra robo de token).
    reuso = client.post(REFRESH, json={"refresh_token": usuario.refresh_token})
    assert reuso.status_code == 401
    # El nuevo sí.
    assert client.post(REFRESH, json={"refresh_token": nuevo["refresh_token"]}).status_code == 200


def test_refresh_con_token_inexistente_da_401(client):
    resp = client.post(REFRESH, json={"refresh_token": "no-existe"})

    assert resp.status_code == 401


def test_refresh_expirado_da_401(client, db, usuario):
    fila = db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == hashear_token(usuario.refresh_token))
    ).scalar_one()
    fila.expira_en = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.commit()

    resp = client.post(REFRESH, json={"refresh_token": usuario.refresh_token})

    assert resp.status_code == 401


# --- Logout -----------------------------------------------------------------
def test_logout_revoca_el_refresh(client, usuario):
    resp = client.post(LOGOUT, json={"refresh_token": usuario.refresh_token})

    assert resp.status_code == 200
    assert resp.json() == {"mensaje": "Sesión cerrada."}
    assert client.post(REFRESH, json={"refresh_token": usuario.refresh_token}).status_code == 401


def test_logout_responde_igual_con_token_desconocido(client):
    """RN-26: no revela si la sesión existía."""
    resp = client.post(LOGOUT, json={"refresh_token": "no-existe"})

    assert resp.status_code == 200


# --- Dependencia de autenticación (aplica a todos los endpoints privados) ----
def test_endpoint_privado_sin_token_o_token_invalido_da_401(client):
    sin_token = client.get("/api/v1/usuarios/me")
    basura = client.get("/api/v1/usuarios/me", headers={"Authorization": "Bearer basura"})
    otro_esquema = client.get("/api/v1/usuarios/me", headers={"Authorization": "Basic abc"})

    for resp in (sin_token, basura, otro_esquema):
        assert resp.status_code == 401
        assert resp.headers["WWW-Authenticate"] == "Bearer"


def test_token_de_usuario_borrado_da_401(client, db, usuario):
    db.delete(db.get(Usuario, usuario.id))
    db.commit()

    resp = client.get("/api/v1/usuarios/me", headers=usuario.headers)

    assert resp.status_code == 401
