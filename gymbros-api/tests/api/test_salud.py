"""Comprobación de vida (`GET /salud`), la misma que usa el deploy en el VPS."""

from app.main import VERSION


def test_salud_responde_ok(client):
    resp = client.get("/salud")

    assert resp.status_code == 200
    assert resp.json() == {"estado": "ok", "servicio": "gymbros-api", "version": VERSION}


def test_swagger_y_openapi_disponibles(client):
    """La documentación interactiva es el banco de pruebas manual del equipo."""
    assert client.get("/docs").status_code == 200
    esquema = client.get("/openapi.json")
    assert esquema.status_code == 200
    assert esquema.json()["info"]["title"] == "GymBros API"


def test_registro_de_usuario_por_fixture(usuario):
    """Humo de la infraestructura: registro + login vía fixtures."""
    assert usuario.access_token
    assert usuario.headers["Authorization"].startswith("Bearer ")
