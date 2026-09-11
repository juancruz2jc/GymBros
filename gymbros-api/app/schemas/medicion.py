"""Esquemas del recurso de mediciones (RF-06, RF-07, RF-08, RF-10, RF-11).

`MedicionResponse` es la salida (registro, historial y detalle).
`MedicionActualizar` es la entrada de `PUT /mediciones/{id}`: solo los campos
editables, con los rangos de RN-03 a RN-06, y **sin `usuario_id`** — una
edición no puede reasignar la medición a otra persona (RN-37).
"""

import uuid
from datetime import date, datetime
from typing import Annotated, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------
# Entrada: Registrar medición (RF-06)
# ---------------------------------------------------------
class MedicionCrear(BaseModel):
    fecha: datetime = Field(..., description="Fecha de la medición (RN-70: no puede ser futura)")
    peso_kg: float = Field(..., gt=0, description="Peso corporal en kg (debe ser mayor a 0)")

    porcentaje_grasa: Optional[float] = Field(None, ge=0, le=100)
    masa_muscular_kg: Optional[float] = Field(None, gt=0)

    circunf_cintura_cm: Optional[float] = Field(None, gt=0)
    circunf_cadera_cm: Optional[float] = Field(None, gt=0)
    circunf_brazo_cm: Optional[float] = Field(None, gt=0)
    circunf_pierna_cm: Optional[float] = Field(None, gt=0)
    circunf_pecho_cm: Optional[float] = Field(None, gt=0)


# ---------------------------------------------------------
# Estructuras de Salida (RF-07, RF-08, RF-10)
# ---------------------------------------------------------
class IMCRespuesta(BaseModel):
    valor: float
    categoria: str


class MedicionResponse(BaseModel):
    """Respuesta unificada para registro, historial y detalle de mediciones."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    usuario_id: Optional[UUID] = None
    fecha: date
    peso_kg: float
    porcentaje_grasa: Optional[float] = None
    masa_muscular_kg: Optional[float] = None

    circunf_cintura_cm: Optional[float] = None
    circunf_cadera_cm: Optional[float] = None
    circunf_brazo_cm: Optional[float] = None
    circunf_pierna_cm: Optional[float] = None
    circunf_pecho_cm: Optional[float] = None

    imc: Optional[float] = None
    creado_en: datetime


class InactividadRespuesta(BaseModel):
    ultima_medicion: Optional[datetime] = None
    dias_desde_ultima_medicion: Optional[int] = None
    esta_inactivo: bool = False

class DiferenciasMedicion(BaseModel):
    peso_kg: Optional[float] = None
    porcentaje_grasa: Optional[float] = None
    masa_muscular_kg: Optional[float] = None
    circunf_cintura_cm: Optional[float] = None
    circunf_cadera_cm: Optional[float] = None
    circunf_brazo_cm: Optional[float] = None
    circunf_pierna_cm: Optional[float] = None
    circunf_pecho_cm: Optional[float] = None
    imc: Optional[float] = None


class MedicionComparativaResponse(BaseModel):
    medicion_anterior: MedicionResponse
    medicion_reciente: MedicionResponse
    diferencias: DiferenciasMedicion


# Topes superiores: son técnicos (capacidad de la columna), no reglas de negocio.
# Las columnas son `NUMERIC(5,2)` (máx. 999.99), salvo `porcentaje_grasa` que es
# `NUMERIC(4,2)` (máx. 99.99).
_MAX_NUMERIC_5_2 = 999.99
# RN-04 dice "0 a 100" inclusivo, pero la columna solo llega a 99.99. Se acota a
# 99.99 como TAPÓN TEMPORAL para que ningún valor válido según el schema falle al
# persistir (un 500). La solución definitiva es una migración que ensanche la
# columna a NUMERIC(5,2); está pendiente de coordinar con el equipo. Ver
# docs/api/api_02_mediciones.md (Limitaciones).
_MAX_GRASA_COLUMNA = 99.99

_Peso = Annotated[float, Field(gt=0, le=_MAX_NUMERIC_5_2)]  # RN-03: peso > 0
_Grasa = Annotated[float, Field(ge=0, le=_MAX_GRASA_COLUMNA)]  # RN-04 (acotado, ver arriba)
_Positivo = Annotated[float, Field(gt=0, le=_MAX_NUMERIC_5_2)]  # RN-05/RN-06: > 0


class MedicionActualizar(BaseModel):
    """Cuerpo de `PUT /mediciones/{id}`.

    Actualización **parcial**: solo se cambian los campos presentes en el JSON;
    los que se omiten quedan como estaban.

    RN-37: no declara `usuario_id`. Con la configuración por defecto de Pydantic
    (`extra="ignore"`) un `usuario_id` que llegue en el cuerpo se descarta en
    silencio, sin reasignar la medición.

    RN-03 a RN-06: los rangos se validan solo cuando el campo viene en la
    petición. Un valor fuera de rango es un 422.
    """

    model_config = ConfigDict(extra="ignore")

    fecha: date | None = None
    peso_kg: _Peso | None = None
    porcentaje_grasa: _Grasa | None = None
    masa_muscular_kg: _Positivo | None = None
    circunf_cintura_cm: _Positivo | None = None
    circunf_cadera_cm: _Positivo | None = None
    circunf_brazo_cm: _Positivo | None = None
    circunf_pierna_cm: _Positivo | None = None
    circunf_pecho_cm: _Positivo | None = None
