"""Lógica de autenticación: registro de usuario (RF-01)."""

from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    crear_access_token,
    generar_refresh_token,
    hashear_password,
)
from app.models.usuario import RefreshToken, Usuario
from app.schemas.auth import RegistroRequest, TokenResponse


class CorreoYaRegistradoError(Exception):
    """El correo ya está en uso (RN-20). El endpoint lo traduce a HTTP 409."""


def registrar_usuario(db: Session, datos: RegistroRequest) -> TokenResponse:
    """Crea la cuenta y deja la sesión iniciada (RN-23): devuelve los tokens.

    RN-20 se resuelve intentando el INSERT y capturando el `IntegrityError` de
    la restricción `unique` sobre `correo`, no con un "consultar y luego
    insertar": dos peticiones simultáneas con el mismo correo pasarían las dos
    la consulta. La base es la única fuente de verdad.
    """
    ahora = datetime.now(timezone.utc)

    # RN-20: sin normalizar, "Juan@x.com" y "juan@x.com" serían cuentas distintas.
    usuario = Usuario(
        correo=datos.correo.strip().lower(),
        hash_password=hashear_password(datos.password),
        nombre=datos.nombre,
        consentimiento_datos=True,
        consentimiento_en=ahora,
    )
    db.add(usuario)

    try:
        db.flush()  # fuerza el INSERT; aquí salta el IntegrityError si el correo existe
    except IntegrityError as exc:
        db.rollback()
        raise CorreoYaRegistradoError(datos.correo) from exc

    valor_refresh, hash_refresh = generar_refresh_token()
    db.add(
        RefreshToken(
            usuario_id=usuario.id,
            token_hash=hash_refresh,  # en la base solo el hash, nunca el valor en claro
            expira_en=ahora + timedelta(days=settings.REFRESH_TOKEN_DIAS),
        )
    )

    db.commit()

    return TokenResponse(
        access_token=crear_access_token(usuario.id),
        refresh_token=valor_refresh,
        expires_in=settings.ACCESS_TOKEN_MINUTOS * 60,
    )
