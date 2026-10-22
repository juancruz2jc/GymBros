from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session  
from app.api.dependencies import get_db, get_current_user
from app.schemas.usuario import UsuarioResponse, UsuarioUpdate
from app.services import usuario_service
from app.models.usuario import Usuario

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

@router.get("/me", response_model=UsuarioResponse)
def obtener_mi_perfil(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user)
):
    return usuario_service.obtener_perfil(db, usuario.id)

@router.put("/me", response_model=UsuarioResponse)
def actualizar_mi_perfil(
    datos: UsuarioUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user)
):
    return usuario_service.actualizar_perfil(db, usuario.id, datos)