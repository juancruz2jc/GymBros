"""Esquemas de salida de ejercicios: catálogo (RF-12) y último registro (RF-20).

RN-38: el catálogo es de solo lectura para el usuario final. No hay esquema de
entrada porque el endpoint no acepta crear ni editar ejercicios; los filtros de
la consulta se declaran como parámetros de query en la capa `api/`.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EjercicioResponse(BaseModel):
    """Un ejercicio tal como lo devuelve `GET /api/v1/ejercicios`.

    No se expone `activo`: el catálogo público solo lista ejercicios activos
    (RN-39), así que el campo sería siempre `true` y solo añadiría ruido.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nombre_es: str
    nombre_en: str
    grupo_muscular: str
    equipo: str
    categoria: str
    gif_url: str | None


class UltimoRegistroResponse(BaseModel):
    """Última serie del usuario en un ejercicio (RF-20, sugerencia de progresión).

    Sale de `GET /api/v1/ejercicios/{id}/ultimo-registro`. Si el usuario nunca
    hizo ese ejercicio, el endpoint responde `200` con cuerpo `null`, no con este
    esquema.
    """

    model_config = ConfigDict(from_attributes=True)

    ejercicio_id: uuid.UUID
    sesion_id: uuid.UUID
    fecha: datetime = Field(description="`iniciada_en` de la sesión donde se hizo la serie.")
    numero_serie: int
    repeticiones_realizadas: int
    peso_usado_kg: float
