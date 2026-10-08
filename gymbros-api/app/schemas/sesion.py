"""Esquemas del recurso de sesiones de entrenamiento (RF-15, RF-17, RF-18).

`SesionIniciar` es la entrada de `POST /sesiones` y `SesionFinalizar` la de
`POST /sesiones/{id}/finalizar`; `SesionResponse` es la salida de ambas y de
`GET /sesiones/activa`.

`CalificacionCrear` es la entrada de `PATCH /sesiones/{id}/calificacion`.
`CalificacionResponse` es la salida: los campos de calificación junto con el id
de la sesión para confirmar la operación.

RN: la calificación es un entero entre 1 y 5 (inclusive). Se rechazan booleanos
explícitamente para evitar que `true`/`false` se coercionen a 1/0.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator


class SesionIniciar(BaseModel):
    """Cuerpo de `POST /sesiones` (RF-15).

    RN-67: `idempotency_key` lo genera la app (p. ej. un UUID) al iniciar la
    sesión en el dispositivo. Si la petición se reintenta tras perder conexión,
    llega la misma clave y el backend devuelve la sesión ya creada en vez de
    duplicarla.
    """

    idempotency_key: str = Field(..., min_length=1, max_length=255)
    rutina_id: Optional[uuid.UUID] = Field(
        None, description="Rutina de la que parte la sesión; omitirla es entrenar libre."
    )
    iniciada_en: Optional[AwareDatetime] = Field(
        None,
        description="Momento real de inicio (sesiones iniciadas sin conexión, RNF-02). "
        "Con zona horaria. Si se omite, se usa la hora del servidor.",
    )


class SesionFinalizar(BaseModel):
    """Cuerpo de `POST /sesiones/{id}/finalizar` (RF-17). Todo opcional."""

    finalizada_en: Optional[AwareDatetime] = Field(
        None,
        description="Momento real de cierre (RNF-02). Con zona horaria. Si se omite, "
        "se usa la hora del servidor.",
    )
    # RN-69: finalizar sin series exige que el usuario lo confirme.
    confirmar_sin_series: bool = False


class SesionResponse(BaseModel):
    """Una sesión de entrenamiento del usuario autenticado."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    rutina_id: Optional[uuid.UUID] = None
    idempotency_key: str
    iniciada_en: datetime
    finalizada_en: Optional[datetime] = None
    duracion_segundos: Optional[int] = None
    calificacion: Optional[int] = None
    nota: Optional[str] = None


class CalificacionCrear(BaseModel):
    """Cuerpo de `PATCH /sesiones/{id}/calificacion`.

    Valida que `calificacion` sea un entero estricto entre 1 y 5 y que no sea
    un booleano disfrazado (Python trata `bool` como subclase de `int`).
    """

    calificacion: int = Field(
        ...,
        ge=1,
        le=5,
        description="Calificación del entrenamiento (1 a 5)",
    )
    nota: Optional[str] = Field(
        None,
        description="Nota de texto libre sobre el entrenamiento",
    )

    @field_validator("calificacion", mode="before")
    @classmethod
    def _rechazar_booleanos(cls, valor):  # noqa: ANN001
        """Rechaza `true`/`false` JSON: Python los coerciona a 1/0 sin error."""
        if isinstance(valor, bool):
            raise ValueError(
                "La calificación debe ser un número entero, no un booleano."
            )
        return valor


class CalificacionResponse(BaseModel):
    """Respuesta tras calificar o actualizar la calificación de una sesión."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    calificacion: int
    nota: Optional[str] = None
    finalizada_en: Optional[datetime] = None
