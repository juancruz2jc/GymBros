"""Lógica de autenticación: registro, login, logout y refresh (RF-01, RF-02)."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    HASH_FICTICIO,
    crear_access_token,
    generar_refresh_token,
    hashear_password,
    hashear_token,
    necesita_rehash,
    verificar_password,
)
from app.models.usuario import RefreshToken, Usuario
from app.schemas.auth import LoginRequest, RegistroRequest, TokenResponse


class CorreoYaRegistradoError(Exception):
    """El correo ya está en uso (RN-20). El endpoint lo traduce a HTTP 409."""


class CredencialesInvalidasError(Exception):
    """Correo o contraseña incorrectos (RN-24). El endpoint -> 401 genérico."""


class RefreshInvalidoError(Exception):
    """El refresh token no existe, está revocado o expiró. El endpoint -> 401."""


def emitir_par_de_tokens(db: Session, usuario: Usuario) -> TokenResponse:
    """Emite un access + un refresh para `usuario`.

    Deja la fila del refresh en la sesión **sin hacer commit**: el que llama
    decide cuándo cerrar la transacción (el registro tras crear el usuario, la
    rotación tras revocar el token viejo). En la base solo va el hash del
    refresh, nunca el valor en claro.
    """
    valor_refresh, hash_refresh = generar_refresh_token()
    db.add(
        RefreshToken(
            usuario_id=usuario.id,
            token_hash=hash_refresh,
            expira_en=datetime.now(timezone.utc)
            + timedelta(days=settings.REFRESH_TOKEN_DIAS),
        )
    )
    return TokenResponse(
        access_token=crear_access_token(usuario.id),
        refresh_token=valor_refresh,
        expires_in=settings.ACCESS_TOKEN_MINUTOS * 60,
    )


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

    respuesta = emitir_par_de_tokens(db, usuario)
    db.commit()
    return respuesta


def autenticar_usuario(db: Session, datos: LoginRequest) -> TokenResponse:
    """Login: verifica credenciales y emite un par de tokens (RN-24, RN-25).

    RN-24: si el correo no existe, se verifica igualmente contra un hash
    ficticio para que la respuesta tarde lo mismo (Argon2 ~100 ms) que cuando sí
    existe, y no se filtre por cronometría qué correos están registrados. El
    error es idéntico en los dos casos.
    """
    correo = datos.correo.strip().lower()
    usuario = db.execute(
        select(Usuario).where(Usuario.correo == correo)
    ).scalar_one_or_none()

    if usuario is None:
        verificar_password(HASH_FICTICIO, datos.password)  # paga el mismo tiempo
        raise CredencialesInvalidasError

    if not verificar_password(usuario.hash_password, datos.password):
        raise CredencialesInvalidasError

    # Si el hash quedó con parámetros más débiles, se regenera al vuelo y el
    # usuario migra sin enterarse.
    if necesita_rehash(usuario.hash_password):
        usuario.hash_password = hashear_password(datos.password)

    respuesta = emitir_par_de_tokens(db, usuario)
    db.commit()
    return respuesta


def cerrar_sesion(db: Session, refresh_token: str) -> None:
    """Logout: revoca el refresh token (RN-26).

    No revela si el token existía o ya estaba revocado: el endpoint responde
    igual en todos los casos.
    """
    fila = db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == hashear_token(refresh_token)
        )
    ).scalar_one_or_none()
    if fila is not None and not fila.revocado:
        fila.revocado = True
        db.commit()


def rotar_refresh_token(db: Session, refresh_token: str) -> TokenResponse:
    """Refresh: canjea un refresh válido por un par nuevo y revoca el viejo.

    La rotación es la defensa: un token robado que se use después de que el
    legítimo ya rotó cae como revocado -> 401.
    """
    fila = db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == hashear_token(refresh_token)
        )
    ).scalar_one_or_none()

    ahora = datetime.now(timezone.utc)
    if fila is None or fila.revocado or fila.expira_en <= ahora:
        raise RefreshInvalidoError

    usuario = db.get(Usuario, fila.usuario_id)
    if usuario is None:  # cuenta borrada con un token todavía vivo
        raise RefreshInvalidoError

    fila.revocado = True
    respuesta = emitir_par_de_tokens(db, usuario)
    db.commit()
    return respuesta
