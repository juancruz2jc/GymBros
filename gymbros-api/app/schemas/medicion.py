from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

# Entrada para registrar medición (RF-06)
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

# Ficha devuelta para el cálculo de IMC (RF-07)
class IMCRespuesta(BaseModel):
    valor: float
    categoria: str

# Salida formateada
class MedicionRespuesta(BaseModel):
    id: UUID
    usuario_id: UUID
    fecha: datetime
    peso_kg: float
    porcentaje_grasa: Optional[float] = None
    masa_muscular_kg: Optional[float] = None
    
    circunf_cintura_cm: Optional[float] = None
    circunf_cadera_cm: Optional[float] = None
    circunf_brazo_cm: Optional[float] = None
    circunf_pierna_cm: Optional[float] = None
    circunf_pecho_cm: Optional[float] = None
    
    imc: Optional[IMCRespuesta] = None
    creado_en: datetime

    class Config:
        from_attributes = True

# Salida para la consulta de alerta por inactividad (RF-10)
class InactividadRespuesta(BaseModel):
    ultima_medicion: Optional[datetime] = None
    dias_desde_ultima_medicion: Optional[int] = None
    esta_inactivo: bool = False