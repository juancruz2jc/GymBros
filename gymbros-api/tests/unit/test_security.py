"""Primitivas de seguridad: contraseñas (RN-22) y tokens (RN-23)."""

import uuid
from datetime import datetime, timedelta, timezone

import jwt

from app.core import security
from app.core.config import settings


def test_hash_de_password_verifica_y_no_guarda_texto_plano():
    hash_ = security.hashear_password("Clave12345")

    assert "Clave12345" not in hash_
    assert hash_.startswith("$argon2id$")
    assert security.verificar_password(hash_, "Clave12345") is True
    assert security.verificar_password(hash_, "otra-clave1") is False


def test_verificar_password_con_hash_ilegible_devuelve_false():
    assert security.verificar_password("no-es-un-hash", "Clave12345") is False


def test_necesita_rehash():
    assert security.necesita_rehash(security.hashear_password("Clave12345")) is False
    assert security.necesita_rehash("no-es-un-hash") is False


def test_access_token_ida_y_vuelta():
    usuario_id = uuid.uuid4()
    token = security.crear_access_token(usuario_id)

    assert security.decodificar_access_token(token) == usuario_id


def _token(payload: dict, secreto: str | None = None) -> str:
    return jwt.encode(payload, secreto or settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def test_access_token_expirado_es_invalido():
    pasado = datetime.now(timezone.utc) - timedelta(minutes=1)
    token = _token({"sub": str(uuid.uuid4()), "exp": pasado})

    assert security.decodificar_access_token(token) is None


def test_access_token_mal_firmado_es_invalido():
    futuro = datetime.now(timezone.utc) + timedelta(minutes=5)
    token = _token({"sub": str(uuid.uuid4()), "exp": futuro}, secreto="x" * 40)

    assert security.decodificar_access_token(token) is None


def test_access_token_sin_sub_o_con_sub_no_uuid_es_invalido():
    futuro = datetime.now(timezone.utc) + timedelta(minutes=5)

    assert security.decodificar_access_token(_token({"exp": futuro})) is None
    assert security.decodificar_access_token(_token({"sub": "no-uuid", "exp": futuro})) is None


def test_access_token_basura_es_invalido():
    assert security.decodificar_access_token("esto.no.es-un-jwt") is None


def test_refresh_token_se_entrega_en_claro_y_se_guarda_hasheado():
    valor, hash_ = security.generar_refresh_token()

    assert valor != hash_
    assert hash_ == security.hashear_token(valor)
    assert len(hash_) == 64  # SHA-256 hex
    assert security.generar_refresh_token()[0] != valor
