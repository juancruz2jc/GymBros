import uuid
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime

# --- ESQUEMAS DE ENTRADA ---

class RutinaEjercicioCreate(BaseModel):
    """Datos para añadir un ejercicio a una rutina"""
    ejercicio_id: uuid.UUID
    orden: int = Field(..., ge=1, description="Orden del ejercicio en la rutina")
    series_objetivo: int = Field(..., ge=1)
    repeticiones_objetivo: int = Field(..., ge=1)
    descanso_segundos: int = Field(..., ge=0)

class RutinaCreate(BaseModel):
    """Datos para crear una nueva rutina completa"""
    nombre: str = Field(..., min_length=1, max_length=100)
    favorita: bool = False
    ejercicios: list[RutinaEjercicioCreate] = Field(..., min_length=1, description="La rutina debe tener al menos un ejercicio")

class RutinaUpdate(BaseModel):
    """Datos para editar una rutina (todo opcional)"""
    nombre: str | None = Field(None, min_length=1, max_length=100)
    favorita: bool | None = None
    ejercicios: list[RutinaEjercicioCreate] | None = None

# --- ESQUEMAS DE SALIDA ---

class RutinaEjercicioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    rutina_id: uuid.UUID
    ejercicio_id: uuid.UUID
    orden: int
    series_objetivo: int
    repeticiones_objetivo: int
    descanso_segundos: int

class RutinaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    usuario_id: uuid.UUID
    nombre: str
    favorita: bool
    creado_en: datetime | None
    actualizado_en: datetime | None
    ejercicios: list[RutinaEjercicioResponse] = []