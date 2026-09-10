"""Dependencias compartidas de FastAPI."""

from collections.abc import Generator

from sqlalchemy.orm import Session

from app.core.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Cede una sesión de base de datos y la cierra al terminar la petición.

    El `finally` es lo que importa: si el endpoint lanza una excepción, sin él
    la sesión queda abierta y su conexión nunca vuelve al pool. Con `def` (no
    `async def`) FastAPI ejecuta el endpoint en un hilo aparte, acorde con el
    acceso a datos síncrono de SQLAlchemy.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
