"""Esquemas del recurso de mediciones."""

from datetime import date, datetime, timezone
from typing import Annotated, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# Límites de los campos numéricos
_MAX_NUMERIC_5_2 = 999.99
_MAX_GRASA_COLUMNA = 99.99

# Evita guardar valores que terminen redondeándose a 0.00
_MIN_NUMERIC_5_2 = 0.01


_Peso = Annotated[float, Field(ge=_MIN_NUMERIC_5_2, le=_MAX_NUMERIC_5_2)]
_Grasa = Annotated[float, Field(ge=0, le=_MAX_GRASA_COLUMNA)]
_Positivo = Annotated[float, Field(ge=_MIN_NUMERIC_5_2, le=_MAX_NUMERIC_5_2)]


# Datos para crear una medición
class MedicionCrear(BaseModel):
    fecha: datetime = Field(
        ...,
        description="Fecha de la medición (no puede ser futura)"
    )

    peso_kg: _Peso = Field(
        ...,
        description="Peso corporal en kg"
    )

    porcentaje_grasa: Optional[_Grasa] = Field(
        None,
        description="Porcentaje de grasa"
    )

    masa_muscular_kg: Optional[_Positivo] = Field(
        None,
        description="Masa muscular en kg"
    )

    circunf_cintura_cm: Optional[_Positivo] = Field(
        None,
        description="Circunferencia de cintura"
    )

    circunf_cadera_cm: Optional[_Positivo] = Field(
        None,
        description="Circunferencia de cadera"
    )

    circunf_brazo_cm: Optional[_Positivo] = Field(
        None,
        description="Circunferencia de brazo"
    )

    circunf_pierna_cm: Optional[_Positivo] = Field(
        None,
        description="Circunferencia de pierna"
    )

    circunf_pecho_cm: Optional[_Positivo] = Field(
        None,
        description="Circunferencia de pecho"
    )

    @field_validator(
        "peso_kg",
        "porcentaje_grasa",
        "masa_muscular_kg",
        "circunf_cintura_cm",
        "circunf_cadera_cm",
        "circunf_brazo_cm",
        "circunf_pierna_cm",
        "circunf_pecho_cm",
        mode="before",
    )
    @classmethod
    def _rechazar_booleanos(cls, valor):
        if isinstance(valor, bool):
            raise ValueError("Los campos numéricos no pueden ser booleanos")
        return valor


# Respuesta del IMC
class IMCRespuesta(BaseModel):
    valor: float
    categoria: str


# Datos que se muestran de una medición
class MedicionResponse(BaseModel):
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


# Datos relacionados con la inactividad (H-10 / GYM-82)
class InactividadRespuesta(BaseModel):
    ultima_medicion: Optional[date] = None
    dias_desde_ultima_medicion: Optional[int] = None
    esta_inactivo: bool = False


# Campos que se pueden editar
class MedicionActualizar(BaseModel):
    # Solo se cambian los campos que se envían
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

    @field_validator(
        "peso_kg",
        "porcentaje_grasa",
        "masa_muscular_kg",
        "circunf_cintura_cm",
        "circunf_cadera_cm",
        "circunf_brazo_cm",
        "circunf_pierna_cm",
        "circunf_pecho_cm",
        mode="before",
    )
    @classmethod
    def _rechazar_booleanos(cls, valor):
        if isinstance(valor, bool):
            raise ValueError("Los campos numéricos no pueden ser booleanos")
        return valor

    # La fecha no puede ser posterior a hoy
    @field_validator("fecha")
    @classmethod
    def _fecha_no_futura(cls, valor: date) -> date:
        if valor > datetime.now(timezone.utc).date():
            raise ValueError("La fecha de medición no puede ser futura")
        return valor