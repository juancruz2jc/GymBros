"""Dependencias compartidas de FastAPI."""

from collections.abc import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import jwt

from app.core.database import SessionLocal
from app.core.config import settings
from app.models.usuario import Usuario

# El esquema de seguridad apunta a la ruta de login 
token_bearer = HTTPBearer()


def get_db() -> Generator[Session, None, None]:
    """Cede una sesión de base de datos y la cierra al terminar la petición."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credenciales: HTTPAuthorizationCredentials = Depends(token_bearer), 
    db: Session = Depends(get_db)
) -> Usuario:
    """Extrae y valida el token JWT, retornando el usuario autenticado."""
    token = credenciales.credentials
    credenciales_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])  
        usuario_id: str = payload.get("sub")
        
        if usuario_id is None:
            raise credenciales_exception
            
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El token ha expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise credenciales_exception

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if usuario is None:
        raise credenciales_exception

    return usuario