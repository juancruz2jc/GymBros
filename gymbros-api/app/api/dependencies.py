"""Dependencias compartidas de FastAPI."""

from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import decodificar_access_token
from app.models.usuario import Usuario


def get_db() -> Generator[Session, None, None]:
    """Cede una sesión de base de datos y la cierra al terminar la petición."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# `auto_error=False`: si el header falta o no es `Bearer`, `HTTPBearer` por
# defecto responde 403; lo desactivamos para dar 401 en todos los casos, igual
# que hace `auth.py`. El esquema aparece como botón "Authorize" en Swagger.
_bearer = HTTPBearer(auto_error=False)

# Mismo error genérico pase lo que pase (token ausente, mal firmado, expirado o
# usuario borrado): no se revela cuál de las condiciones falló.
_NO_AUTENTICADO = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="No autenticado.",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    credenciales: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Usuario:
    """Usuario dueño del access token en `Authorization: Bearer <token>`.

    Lanza 401 si el token falta, está mal formado, mal firmado, expiró, o si el
    usuario del `sub` ya no existe. El `usuario_id` SIEMPRE sale de aquí (del
    token), nunca de la URL ni del body.
    """
    if credenciales is None or credenciales.scheme.lower() != "bearer":
        raise _NO_AUTENTICADO

    usuario_id = decodificar_access_token(credenciales.credentials)
    if usuario_id is None:
        raise _NO_AUTENTICADO

    usuario = db.get(Usuario, usuario_id)
    if usuario is None:  # token válido pero la cuenta ya no está
        raise _NO_AUTENTICADO
    return usuario
