"""Esquemas de entrada y salida para autenticación (RF-01)."""

import re

from pydantic import BaseModel, EmailStr, Field, field_validator

# RN-21: mínimo 8 caracteres, al menos una letra y al menos un número.
_TIENE_LETRA = re.compile(r"[A-Za-z]")
_TIENE_NUMERO = re.compile(r"\d")


class RegistroRequest(BaseModel):
    """Cuerpo de `POST /auth/registro`. No incluye `usuario_id`."""

    correo: EmailStr
    password: str = Field(min_length=8, max_length=128)
    nombre: str = Field(min_length=1, max_length=100)
    consentimiento_datos: bool

    @field_validator("password")
    @classmethod
    def _password_cumple_rn21(cls, valor: str) -> str:
        if not _TIENE_LETRA.search(valor) or not _TIENE_NUMERO.search(valor):
            raise ValueError(
                "La contraseña debe incluir al menos una letra y un número."
            )
        return valor

    @field_validator("nombre")
    @classmethod
    def _nombre_no_vacio(cls, valor: str) -> str:
        limpio = valor.strip()
        if not limpio:
            raise ValueError("El nombre no puede estar vacío.")
        return limpio

    @field_validator("consentimiento_datos")
    @classmethod
    def _exige_consentimiento(cls, valor: bool) -> bool:
        if valor is not True:
            raise ValueError(
                "Debes aceptar el tratamiento de datos para registrarte (Ley 1581)."
            )
        return valor


class TokenResponse(BaseModel):
    """Par de tokens que se devuelve tras un registro o login correcto (RN-23)."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # segundos de vida del access_token
