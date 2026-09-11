from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Dict, Any
from uuid import UUID

class UsuarioResponse(BaseModel):
    id: UUID
    correo: str
    nombre: str
    sexo: Optional[str] = None
    altura_cm: Optional[int] = None
    foto_url: Optional[str] = None
    codigo_gimnasio: Optional[str] = None
    tiene_experiencia_previa: Optional[bool] = None
    preferencias_notificacion: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    sexo: Optional[str] = Field(None, max_length=20)
    altura_cm: Optional[int] = Field(None, gt=50, lt=300)
    foto_url: Optional[str] = Field(None, max_length=500)
    preferencias_notificacion: Optional[Dict[str, Any]] = None