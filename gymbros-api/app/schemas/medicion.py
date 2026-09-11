"""Esquemas de salida del historial de mediciones (RF-08).

Este endpoint es de solo lectura: el alta y la edición de mediciones son otra
historia. Por eso aquí solo se declara la forma de salida, sin esquema de
entrada.
"""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class MedicionResponse(BaseModel):
    """Una medición del historial del usuario autenticado.

    Los campos numéricos se exponen como número JSON (no string) para que el
    cliente de gráficas los consuma directo.

    `imc` es un valor **calculado** (RN-12), no una columna: sale de `peso_kg` y
    de la altura vigente del usuario (`usuarios.altura_cm`), no de la altura que
    tuviera en la fecha de la medición (RN-30). Es `null` si el usuario no tiene
    altura registrada (RN-09).

    `creado_en` se incluye a propósito: deja ver cuándo se registró una medición,
    que puede ser muy posterior a su `fecha` (RN-34).
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    fecha: date
    peso_kg: float
    imc: float | None = None
    porcentaje_grasa: float | None = None
    masa_muscular_kg: float | None = None
    circunf_cintura_cm: float | None = None
    circunf_cadera_cm: float | None = None
    circunf_brazo_cm: float | None = None
    circunf_pierna_cm: float | None = None
    circunf_pecho_cm: float | None = None
    creado_en: datetime
