"""Esquemas de salida del catálogo de ejercicios (RF-12).

RN-38: el catálogo es de solo lectura para el usuario final. No hay esquema de
entrada porque el endpoint no acepta crear ni editar ejercicios; los filtros de
la consulta se declaran como parámetros de query en la capa `api/`.
"""

import uuid

from pydantic import BaseModel, ConfigDict


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
