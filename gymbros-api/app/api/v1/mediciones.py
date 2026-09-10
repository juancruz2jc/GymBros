from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_db, get_current_user
from app.models.usuario import Usuario
from app.schemas.medicion import MedicionCrear, MedicionRespuesta, InactividadRespuesta
from app.services import medicion_service

router = APIRouter(prefix="/mediciones", tags=["Mediciones"])

@router.post("/", response_model=MedicionRespuesta, status_code=status.HTTP_201_CREATED)
def registrar_medicion(
    datos: MedicionCrear,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user)
):
    try:
        medicion, imc = medicion_service.crear_medicion(db, usuario_actual, datos)
        # Adaptación para adjuntar el imc dinamico a la respuesta
        respuesta = MedicionRespuesta.model_validate(medicion)
        respuesta.imc = imc
        return respuesta
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/inactividad", response_model=InactividadRespuesta)
def consultar_inactividad(
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user)
):
    return medicion_service.obtener_estado_inactividad(db, usuario_actual)