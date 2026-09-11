import uuid
from datetime import date, datetime
from typing import Optional
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
    """Respuesta unificada para historial y registro de mediciones."""
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