"""Esquemas del recurso de sesiones de entrenamiento (RF-18).

`CalificacionCrear` es la entrada de `PATCH /sesiones/{id}/calificacion`.
`CalificacionResponse` es la salida: los campos de calificación junto con el id
de la sesión para confirmar la operación.

RN: la calificación es un entero entre 1 y 5 (inclusive). Se rechazan booleanos
explícitamente para evitar que `true`/`false` se coercionen a 1/0.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


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
