"""Primitivas de seguridad: hash de contraseñas y emisión de tokens.

RN-22: la contraseña en claro no se registra en logs ni se almacena. Solo entra
a `hashear_password` / `verificar_password` y no sale de este módulo.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import settings

# Instancia única. argon2-cffi usa Argon2id por defecto (RN-22) y sus parámetros
# de coste por defecto son los que recomienda OWASP; no hace falta configurarlos.
_hasher = PasswordHasher()

# Hash de una contraseña que no existe, calculado una vez al importar. El login
# lo usa cuando el correo no está registrado: verifica la contraseña contra este
# hash para pagar el mismo coste de Argon2 (~100 ms) que la ruta en la que el
# usuario sí existe, y así no revelar por cronometría qué correos hay (RN-24).
HASH_FICTICIO = _hasher.hash(secrets.token_urlsafe(32))


def hashear_password(password: str) -> str:
    """Devuelve el hash Argon2id de la contraseña (incluye sal y parámetros)."""
    return _hasher.hash(password)


def verificar_password(hash_almacenado: str, password: str) -> bool:
    """Indica si la contraseña coincide con el hash. No lanza."""
    try:
        return _hasher.verify(hash_almacenado, password)
    except (VerificationError, InvalidHashError):
        return False


def necesita_rehash(hash_almacenado: str) -> bool:
    """Indica si el hash se generó con parámetros más débiles que los actuales.

    Se llama tras un `verificar_password` correcto: si devuelve `True`, hay que
    volver a hashear la contraseña en claro con `hashear_password` y guardar el
    nuevo hash. Así los usuarios antiguos migran solos cuando se suben los
    parámetros de Argon2. No lanza: un hash ilegible devuelve `False`.
    """
    try:
        return _hasher.check_needs_rehash(hash_almacenado)
    except InvalidHashError:
        return False


def crear_access_token(usuario_id: UUID | str) -> str:
    """JWT de acceso firmado con `JWT_SECRET` (HS256 por defecto).

    `sub` va como string: lo exigen el RFC 7519 y PyJWT >= 2.10 al decodificar.
    """
    ahora = datetime.now(timezone.utc)
    payload = {
        "sub": str(usuario_id),
        "iat": ahora,
        "exp": ahora + timedelta(minutes=settings.ACCESS_TOKEN_MINUTOS),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decodificar_access_token(token: str) -> UUID | None:
    """`usuario_id` que lleva un access token válido, o `None` si no lo es.

    Inversa de `crear_access_token`: verifica la firma (HS256 con `JWT_SECRET`) y
    la expiración (`exp`). Devuelve `None` —no lanza, igual que
    `verificar_password`— si el token está mal firmado, expiró, le falta `sub` o
    `exp`, o `sub` no es un UUID. Quien llama decide qué responder: la
    dependencia `get_current_user` lo traduce a 401.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
    except jwt.InvalidTokenError:
        # Cubre firma inválida, token expirado (ExpiredSignatureError) y
        # malformado: todas heredan de InvalidTokenError.
        return None

    try:
        return UUID(str(payload["sub"]))
    except (KeyError, ValueError):
        return None


def hashear_token(valor: str) -> str:
    """SHA-256 hex de un token opaco. Se usa al emitirlo (para guardar el hash)
    y en cada petición que lo trae (para buscar la fila por hash).

    SHA-256 y no Argon2: son 256 bits aleatorios, no hay nada que adivinar por
    fuerza bruta y la lentitud de Argon2 solo añadiría latencia en cada lookup.
    """
    return hashlib.sha256(valor.encode()).hexdigest()


def generar_refresh_token() -> tuple[str, str]:
    """Genera un refresh token opaco. Devuelve `(valor_en_claro, hash_sha256_hex)`.

    El valor en claro se entrega al cliente; en la base solo se guarda el hash.
    """
    valor = secrets.token_urlsafe(32)
    return valor, hashear_token(valor)
