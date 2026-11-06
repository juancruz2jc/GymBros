"""Base compartida de las pruebas automatizadas de GymBros API.

Cómo funciona (resumen; detalle en el README del backend, sección "Pruebas"):

1. Las pruebas corren contra un **PostgreSQL desechable**, nunca contra la base
   compartida de Supabase. La URL sale de `TEST_DATABASE_URL` (por defecto un
   contenedor local en el puerto 55432). Si la URL apunta a Supabase o a una base
   cuyo nombre no contiene "test", la ejecución se aborta antes de tocar nada.
2. Al iniciar, se borra el esquema `public` de esa base y se reconstruye con
   `alembic upgrade head`: las migraciones quedan probadas en cada ejecución.
3. Cada prueba corre dentro de una transacción que se revierte al final. Los
   `commit()` de los servicios solo liberan un SAVEPOINT interno, así que nada
   persiste entre pruebas y el orden de ejecución no importa.
4. `--verificar-rutas` (lo usa el CI) hace fallar la ejecución si algún endpoint
   de la app no fue llamado por ninguna prueba. Así un módulo nuevo sin pruebas
   no llega a `dev`.
"""

import os
import uuid
from collections.abc import Callable, Generator, Iterator
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

import pytest

# ---------------------------------------------------------------------------
# Entorno de prueba. DEBE fijarse antes de importar `app`: `app.core.config`
# lee la configuración al importarse. Se sobrescribe (no `setdefault`) a
# propósito: una variable de entorno gana sobre el `.env`, así que el `.env`
# local con la URL de Supabase nunca se usa durante las pruebas.
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg2://gymbros:gymbros@localhost:55432/gymbros_test",
)


def _validar_url_de_prueba(url: str) -> None:
    """Corta la ejecución si la URL no parece una base desechable de pruebas.

    Las pruebas borran el esquema completo: apuntarlas a una base real sería
    destruir datos del equipo.
    """
    from sqlalchemy.engine import make_url

    partes = make_url(url)
    if "supabase" in (partes.host or "") or "test" not in (partes.database or ""):
        raise pytest.UsageError(
            f"TEST_DATABASE_URL no parece una base de pruebas ({partes.host}/{partes.database}). "
            "Debe ser un PostgreSQL desechable cuyo nombre contenga 'test'; "
            "las pruebas borran y recrean su esquema."
        )


_validar_url_de_prueba(TEST_DATABASE_URL)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["JWT_SECRET"] = "secreto-solo-para-pruebas-automatizadas-0123456789"
os.environ["DB_POOL_SIZE"] = "2"
os.environ["DB_MAX_OVERFLOW"] = "0"

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.routing import APIRoute  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.engine import Engine  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402
from sqlalchemy.pool import NullPool  # noqa: E402

from app.api.dependencies import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.entrenamiento import Ejercicio  # noqa: E402

RAIZ_API = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZONA_COLOMBIA = ZoneInfo("America/Bogota")
PASSWORD_PRUEBA = "Prueba12345"


def hoy_colombia() -> date:
    """El "hoy" que usa la API (día calendario en Bogotá, no en UTC)."""
    return datetime.now(ZONA_COLOMBIA).date()


# ---------------------------------------------------------------------------
# Registro de rutas llamadas (para --verificar-rutas)
# ---------------------------------------------------------------------------
RUTAS_LLAMADAS: set[tuple[str, str]] = set()


class _RegistroDeRutas:
    """Middleware ASGI que anota qué ruta de FastAPI atendió cada petición.

    Starlette guarda en `scope["route"]` la ruta que hizo match; se lee después
    de atender la petición, así que cuenta aunque la respuesta sea 4xx.
    """

    def __init__(self, app_asgi: Any) -> None:
        self.app = app_asgi

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        try:
            await self.app(scope, receive, send)
        finally:
            ruta = scope.get("route")
            if scope.get("type") == "http" and isinstance(ruta, APIRoute):
                RUTAS_LLAMADAS.add((scope["method"], ruta.path))


app.add_middleware(_RegistroDeRutas)


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Marca cada prueba según su carpeta: `pytest -m unit` o `pytest -m api`."""
    for item in items:
        carpeta = item.path.parent.name
        if carpeta in {"unit", "api"}:
            item.add_marker(carpeta)


def rutas_de_la_app() -> set[tuple[str, str]]:
    """Todos los endpoints propios de la app como (método, plantilla de ruta)."""
    return {
        (metodo, ruta.path)
        for ruta in app.routes
        if isinstance(ruta, APIRoute)
        for metodo in ruta.methods
        if metodo not in {"HEAD", "OPTIONS"}
    }


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--verificar-rutas",
        action="store_true",
        default=False,
        help="Falla si algún endpoint de la app no fue llamado por ninguna prueba.",
    )


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    if not session.config.getoption("--verificar-rutas") or exitstatus != 0:
        return
    sin_probar = sorted(rutas_de_la_app() - RUTAS_LLAMADAS, key=lambda r: (r[1], r[0]))
    if sin_probar:
        lineas = "\n".join(f"  - {metodo} {ruta}" for metodo, ruta in sin_probar)
        reporter = session.config.pluginmanager.get_plugin("terminalreporter")
        mensaje = (
            "\nENDPOINTS SIN PRUEBAS (--verificar-rutas):\n"
            f"{lineas}\n"
            "Agrega al menos una prueba en tests/api/ que llame a cada uno.\n"
        )
        if reporter is not None:
            reporter.write_line(mensaje, red=True, bold=True)
        else:  # pragma: no cover
            print(mensaje)
        session.exitstatus = pytest.ExitCode.TESTS_FAILED


# ---------------------------------------------------------------------------
# Base de datos
# ---------------------------------------------------------------------------
def _config_alembic() -> Config:
    cfg = Config(os.path.join(RAIZ_API, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(RAIZ_API, "alembic"))
    return cfg


def _reiniciar_esquema(engine: Engine) -> None:
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    """Motor contra la base de pruebas, con el esquema recién migrado."""
    motor = create_engine(TEST_DATABASE_URL, poolclass=NullPool)
    _reiniciar_esquema(motor)
    command.upgrade(_config_alembic(), "head")
    yield motor
    motor.dispose()


@pytest.fixture
def db(engine: Engine) -> Iterator[Session]:
    """Sesión de base de datos aislada: todo lo que haga la prueba se revierte."""
    conexion = engine.connect()
    transaccion = conexion.begin()
    sesion = Session(
        bind=conexion,
        join_transaction_mode="create_savepoint",
        autoflush=False,
        expire_on_commit=False,
    )
    try:
        yield sesion
    finally:
        sesion.close()
        transaccion.rollback()
        conexion.close()


@pytest.fixture
def client(db: Session) -> Iterator[TestClient]:
    """Cliente HTTP de la API que usa la sesión aislada de la prueba."""

    def _get_db_de_prueba() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = _get_db_de_prueba
    try:
        with TestClient(app) as cliente:
            yield cliente
    finally:
        app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------------
# Usuarios autenticados
# ---------------------------------------------------------------------------
@dataclass
class UsuarioDePrueba:
    id: uuid.UUID
    correo: str
    password: str
    access_token: str
    refresh_token: str

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.access_token}"}


@pytest.fixture
def crear_usuario(client: TestClient) -> Callable[..., UsuarioDePrueba]:
    """Fábrica: registra un usuario por la API y devuelve sus tokens."""

    def _crear(
        correo: str | None = None,
        password: str = PASSWORD_PRUEBA,
        nombre: str = "Usuario de prueba",
    ) -> UsuarioDePrueba:
        correo = correo or f"prueba-{uuid.uuid4().hex[:10]}@gymbros-pruebas.com"
        resp = client.post(
            "/api/v1/auth/registro",
            json={
                "correo": correo,
                "password": password,
                "nombre": nombre,
                "consentimiento_datos": True,
            },
        )
        assert resp.status_code == 201, resp.text
        tokens = resp.json()
        perfil = client.get(
            "/api/v1/usuarios/me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert perfil.status_code == 200, perfil.text
        return UsuarioDePrueba(
            id=uuid.UUID(perfil.json()["id"]),
            correo=correo.lower(),
            password=password,
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
        )

    return _crear


@pytest.fixture
def usuario(crear_usuario: Callable[..., UsuarioDePrueba]) -> UsuarioDePrueba:
    return crear_usuario()


@pytest.fixture
def otro_usuario(crear_usuario: Callable[..., UsuarioDePrueba]) -> UsuarioDePrueba:
    """Segundo usuario, para comprobar que nadie ve ni toca datos ajenos (RN-60)."""
    return crear_usuario()


# ---------------------------------------------------------------------------
# Datos de dominio
# ---------------------------------------------------------------------------
@pytest.fixture
def crear_ejercicio(db: Session) -> Callable[..., Ejercicio]:
    """Fábrica: inserta un ejercicio en el catálogo (el catálogo no tiene API de alta)."""

    def _crear(**campos: Any) -> Ejercicio:
        datos = {
            "nombre_es": f"Ejercicio {uuid.uuid4().hex[:6]}",
            "nombre_en": "Test exercise",
            "grupo_muscular": "pecho",
            "equipo": "barra",
            "categoria": "compuesto",
            "gif_url": None,
            "activo": True,
        }
        datos.update(campos)
        ejercicio = Ejercicio(**datos)
        db.add(ejercicio)
        db.commit()
        return ejercicio

    return _crear


@pytest.fixture
def ejercicio(crear_ejercicio: Callable[..., Ejercicio]) -> Ejercicio:
    return crear_ejercicio()


@pytest.fixture
def crear_rutina(client: TestClient) -> Callable[..., dict]:
    """Fábrica: crea una rutina por la API. `ejercicios` es una lista de Ejercicio."""

    def _crear(
        usuario: UsuarioDePrueba,
        ejercicios: list[Ejercicio],
        nombre: str = "Rutina de prueba",
        favorita: bool = False,
    ) -> dict:
        resp = client.post(
            "/api/v1/rutinas",
            headers=usuario.headers,
            json={
                "nombre": nombre,
                "favorita": favorita,
                "ejercicios": [
                    {
                        "ejercicio_id": str(ej.id),
                        "orden": i,
                        "series_objetivo": 3,
                        "repeticiones_objetivo": 10,
                        "descanso_segundos": 90,
                    }
                    for i, ej in enumerate(ejercicios, start=1)
                ],
            },
        )
        assert resp.status_code == 201, resp.text
        return resp.json()

    return _crear


@pytest.fixture
def iniciar_sesion(client: TestClient) -> Callable[..., dict]:
    """Fábrica: inicia una sesión de entrenamiento por la API."""

    def _iniciar(usuario: UsuarioDePrueba, **campos: Any) -> dict:
        cuerpo = {"idempotency_key": str(uuid.uuid4())}
        cuerpo.update({k: (str(v) if isinstance(v, uuid.UUID) else v) for k, v in campos.items()})
        resp = client.post("/api/v1/sesiones", headers=usuario.headers, json=cuerpo)
        assert resp.status_code == 201, resp.text
        return resp.json()

    return _iniciar


@pytest.fixture
def registrar_series(client: TestClient) -> Callable[..., list[dict]]:
    """Fábrica: registra series en una sesión activa por la API."""

    def _registrar(usuario: UsuarioDePrueba, sesion_id: str, series: list[dict]) -> list[dict]:
        resp = client.post(
            f"/api/v1/sesiones/{sesion_id}/series",
            headers=usuario.headers,
            json={"series": series},
        )
        assert resp.status_code == 201, resp.text
        return resp.json()

    return _registrar


@pytest.fixture
def sesion_finalizada(
    client: TestClient,
    iniciar_sesion: Callable[..., dict],
    registrar_series: Callable[..., list[dict]],
) -> Callable[..., dict]:
    """Fábrica: sesión completa (inicio + series + fin). Devuelve la sesión finalizada.

    `series` es una lista de (ejercicio, numero_serie, repeticiones, peso).
    """

    def _crear(
        usuario: UsuarioDePrueba,
        series: list[tuple[Ejercicio, int, int, float]],
        iniciada_en: str = "2026-01-10T10:00:00-05:00",
        finalizada_en: str = "2026-01-10T11:00:00-05:00",
        **campos: Any,
    ) -> dict:
        sesion = iniciar_sesion(usuario, iniciada_en=iniciada_en, **campos)
        if series:
            registrar_series(
                usuario,
                sesion["id"],
                [
                    {
                        "ejercicio_id": str(ej.id),
                        "numero_serie": n,
                        "repeticiones_realizadas": reps,
                        "peso_usado_kg": peso,
                        "orden": i,
                    }
                    for i, (ej, n, reps, peso) in enumerate(series, start=1)
                ],
            )
        resp = client.post(
            f"/api/v1/sesiones/{sesion['id']}/finalizar",
            headers=usuario.headers,
            json={"finalizada_en": finalizada_en, "confirmar_sin_series": not series},
        )
        assert resp.status_code == 200, resp.text
        return resp.json()

    return _crear


@pytest.fixture
def crear_medicion(client: TestClient) -> Callable[..., dict]:
    """Fábrica: registra una medición por la API."""

    def _crear(usuario: UsuarioDePrueba, fecha: date | None = None, **campos: Any) -> dict:
        fecha = fecha or hoy_colombia()
        cuerpo = {"fecha": f"{fecha.isoformat()}T08:00:00-05:00", "peso_kg": 70.0}
        cuerpo.update(campos)
        resp = client.post("/api/v1/mediciones", headers=usuario.headers, json=cuerpo)
        assert resp.status_code == 201, resp.text
        return resp.json()

    return _crear
