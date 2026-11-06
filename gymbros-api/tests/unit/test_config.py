"""Validación de la configuración de arranque (`app.core.config.Settings`)."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import JWT_SECRET_DE_EJEMPLO, Settings

_URL = "postgresql+psycopg2://u:p@localhost:5432/db_test"


def _settings(**campos) -> Settings:
    # `_env_file=None`: que la prueba no dependa del `.env` local.
    return Settings(_env_file=None, **campos)


def test_rechaza_el_secreto_de_ejemplo():
    with pytest.raises(ValidationError, match="valor de ejemplo"):
        _settings(DATABASE_URL=_URL, JWT_SECRET=JWT_SECRET_DE_EJEMPLO)


def test_rechaza_secreto_corto():
    with pytest.raises(ValidationError, match="al menos 32"):
        _settings(DATABASE_URL=_URL, JWT_SECRET="corto")


def test_acepta_secreto_valido_y_aplica_defaults():
    cfg = _settings(DATABASE_URL=_URL, JWT_SECRET="s" * 32)

    assert cfg.JWT_ALGORITHM == "HS256"
    assert cfg.ACCESS_TOKEN_MINUTOS == 15
    assert cfg.REFRESH_TOKEN_DIAS == 30


def test_el_ejemplo_del_env_coincide_con_la_constante():
    """config.py exige que JWT_SECRET_DE_EJEMPLO sea idéntico al de .env.example;
    si alguien edita uno solo, la validación deja de dispararse sin avisar."""
    ejemplo = (Path(__file__).resolve().parents[2] / ".env.example").read_text(encoding="utf-8")
    assert f"JWT_SECRET={JWT_SECRET_DE_EJEMPLO}" in ejemplo
