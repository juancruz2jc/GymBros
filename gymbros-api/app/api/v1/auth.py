"""Endpoints de autenticación (RF-01)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.auth import RegistroRequest, TokenResponse
from app.services.auth_service import CorreoYaRegistradoError, registrar_usuario

router = APIRouter(prefix="/auth", tags=["auth"])


# `def`, no `async def`: el servicio hace acceso a datos síncrono (ver main.py).
@router.post(
    "/registro",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un usuario y abrir sesión",
)
def registro(datos: RegistroRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Crea la cuenta y devuelve el par de tokens (RN-23: deja sesión iniciada)."""
    try:
        return registrar_usuario(db, datos)
    except CorreoYaRegistradoError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El correo ya está registrado.",
        )
