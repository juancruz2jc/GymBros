"""Endpoints de autenticación (RF-01, RF-02)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.auth import (
    LoginRequest,
    MensajeResponse,
    RefreshTokenRequest,
    RegistroRequest,
    TokenResponse,
)
from app.services.auth_service import (
    CorreoYaRegistradoError,
    CredencialesInvalidasError,
    RefreshInvalidoError,
    autenticar_usuario,
    cerrar_sesion,
    registrar_usuario,
    rotar_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# Mensajes genéricos: no revelan si el fallo fue por el correo o por la contraseña.
_ERROR_CREDENCIALES = "Correo o contraseña incorrectos."
_ERROR_REFRESH = "Refresh token inválido o expirado."


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


@router.post("/login", response_model=TokenResponse, summary="Iniciar sesión")
def login(datos: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Verifica credenciales y devuelve un par de tokens nuevo (RN-24, RN-25)."""
    try:
        return autenticar_usuario(db, datos)
    except CredencialesInvalidasError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_ERROR_CREDENCIALES,
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/logout", response_model=MensajeResponse, summary="Cerrar sesión")
def logout(datos: RefreshTokenRequest, db: Session = Depends(get_db)) -> MensajeResponse:
    """Revoca el refresh token. Responde igual exista o no la sesión (RN-26)."""
    cerrar_sesion(db, datos.refresh_token)
    return MensajeResponse(mensaje="Sesión cerrada.")


@router.post("/refresh", response_model=TokenResponse, summary="Renovar la sesión")
def refresh(datos: RefreshTokenRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Canjea un refresh válido por un par nuevo y revoca el anterior (rotación)."""
    try:
        return rotar_refresh_token(db, datos.refresh_token)
    except RefreshInvalidoError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_ERROR_REFRESH,
            headers={"WWW-Authenticate": "Bearer"},
        )
