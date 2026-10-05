import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_db, get_current_user
from app.schemas.rutina import RutinaCreate, RutinaResponse
from app.services import rutina_service



router = APIRouter(prefix="/rutinas", tags=["rutinas"])

@router.post("", response_model=RutinaResponse, status_code=status.HTTP_201_CREATED)
def crear_rutina(
    rutina_in: RutinaCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """RF-13: Crea una nueva rutina propia con sus ejercicios."""
    return rutina_service.crear_rutina(db=db, rutina_in=rutina_in, usuario_id=current_user.id)

@router.get("", response_model=list[RutinaResponse])
def listar_rutinas(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Lista todas las rutinas propias del usuario autenticado."""
    return rutina_service.listar_rutinas_usuario(db=db, usuario_id=current_user.id)

@router.delete("/{rutina_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_rutina(
    rutina_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """RF-14: Elimina una rutina propia."""
    exito = rutina_service.eliminar_rutina(db=db, rutina_id=rutina_id, usuario_id=current_user.id)
    if not exito:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Rutina no encontrada o no tienes permisos"
        )
    return None

@router.post("/{rutina_id}/duplicar", response_model=RutinaResponse, status_code=status.HTTP_201_CREATED)
def endpoint_duplicar_rutina(
    rutina_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    nueva_rutina = rutina_service.duplicar_rutina(db=db, rutina_id=rutina_id, usuario_id=current_user.id)
    
    if not nueva_rutina:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Rutina no encontrada o no tienes permisos"
        )
        
    return nueva_rutina