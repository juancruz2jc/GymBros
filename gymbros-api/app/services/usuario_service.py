from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioUpdate
from uuid import UUID

def obtener_perfil(db: Session, usuario_id: UUID) -> Usuario:
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario

def actualizar_perfil(db: Session, usuario_id: UUID, datos: UsuarioUpdate) -> Usuario:
    usuario = obtener_perfil(db, usuario_id)
    
    datos_dict = datos.model_dump(exclude_unset=True)
    for clave, valor in datos_dict.items():
        setattr(usuario, clave, valor)
        
    db.commit()
    db.refresh(usuario)
    return usuario