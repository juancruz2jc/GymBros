"""Esquemas del recurso de mediciones (RF-06, RF-07, RF-08, RF-10, RF-11).

`MedicionResponse` es la salida (registro, historial y detalle).
`MedicionActualizar` es la entrada de `PUT /mediciones/{id}`: solo los campos
editables, con los rangos de RN-03 a RN-06, y **sin `usuario_id`** — una
edición no puede reasignar la medición a otra persona (RN-37).
"""

from datetime import date, datetime
from typing import Annotated, Optional
from uuid import UUID
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, field_validator

# H-05: "hoy" es el día en Colombia, no en UTC (después de las 7 p. m. UTC ya
# es el día siguiente).
_ZONA_COLOMBIA = ZoneInfo("America/Bogota")

# Topes superiores: son técnicos (capacidad de la columna), no reglas de negocio.
# Todas las columnas de medidas son `NUMERIC(5,2)` (máx. 999.99).
_MAX_NUMERIC_5_2 = 999.99
# GYM-176: mínimo representable en `NUMERIC(5,2)`. Con `gt=0`, un `0.001` pasaba
# la validación y se guardaba como `0.00`.
_MIN_NUMERIC_5_2 = 0.01

_Peso = Annotated[float, Field(ge=_MIN_NUMERIC_5_2, le=_MAX_NUMERIC_5_2)]  # RN-03: peso > 0
_Grasa = Annotated[float, Field(ge=0, le=100)]  # RN-04: 0 a 100 inclusive
_Positivo = Annotated[float, Field(ge=_MIN_NUMERIC_5_2, le=_MAX_NUMERIC_5_2)]  # RN-05/RN-06: > 0

_CAMPOS_NUMERICOS = (
    "peso_kg",
    "porcentaje_grasa",
    "masa_muscular_kg",
    "circunf_cintura_cm",
    "circunf_cadera_cm",
    "circunf_brazo_cm",
    "circunf_pierna_cm",
    "circunf_pecho_cm",
)


def _rechazar_booleano(valor):  # noqa: ANN001, ANN202
    """H-09: Pydantic convierte `true`/`false` JSON en 1/0 sin error."""
    if isinstance(valor, bool):
        raise ValueError("Los campos numéricos no pueden ser booleanos.")
    return valor


# ---------------------------------------------------------
# Entrada: Registrar medición (RF-06)
# ---------------------------------------------------------
class MedicionCrear(BaseModel):
    fecha: datetime = Field(..., description="Fecha de la medición (RN-70: no puede ser futura)")
    peso_kg: _Peso = Field(..., description="Peso corporal en kg (debe ser mayor a 0)")

    porcentaje_grasa: Optional[_Grasa] = None
    masa_muscular_kg: Optional[_Positivo] = None

    circunf_cintura_cm: Optional[_Positivo] = None
    circunf_cadera_cm: Optional[_Positivo] = None
    circunf_brazo_cm: Optional[_Positivo] = None
    circunf_pierna_cm: Optional[_Positivo] = None
    circunf_pecho_cm: Optional[_Positivo] = None

    @field_validator(*_CAMPOS_NUMERICOS, mode="before")
    @classmethod
    def _sin_booleanos(cls, valor):  # noqa: ANN001, ANN206
        return _rechazar_booleano(valor)


# ---------------------------------------------------------
# Estructuras de Salida (RF-07, RF-08, RF-10)
# ---------------------------------------------------------
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
    # RN-13: `bajo_peso`, `normal`, `sobrepeso` u `obesidad`; null si no hay IMC.
    categoria_imc: Optional[str] = None
    creado_en: datetime


class InactividadRespuesta(BaseModel):
    ultima_medicion: Optional[date] = None  # H-10: la columna es `Date`
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


class MedicionActualizar(BaseModel):
    """Cuerpo de `PUT /mediciones/{id}`.

    Actualización **parcial**: solo se cambian los campos presentes en el JSON;
    los que se omiten quedan como estaban.

    RN-37: no declara `usuario_id`. Con la configuración por defecto de Pydantic
    (`extra="ignore"`) un `usuario_id` que llegue en el cuerpo se descarta en
    silencio, sin reasignar la medición.

    RN-03 a RN-06 y RN-70: los rangos y la fecha se validan solo cuando el
    campo viene en la petición. Un valor fuera de rango o una fecha futura es
    un 422.
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

    @field_validator(*_CAMPOS_NUMERICOS, mode="before")
    @classmethod
    def _sin_booleanos(cls, valor):  # noqa: ANN001, ANN206
        return _rechazar_booleano(valor)

    # RN-70 (GYM-169): el POST ya lo validaba en `crear_medicion`; el PUT no.
    @field_validator("fecha")
    @classmethod
    def _fecha_no_futura(cls, valor: date | None) -> date | None:
        if valor is not None and valor > datetime.now(_ZONA_COLOMBIA).date():
            raise ValueError("La fecha de medición no puede ser futura.")
        return valor
