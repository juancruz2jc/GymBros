"""Endpoints para la gestión de mediciones corporales (RF-06, RF-07, RF-08, RF-10)."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.usuario import Usuario
from app.schemas.medicion import (
    InactividadRespuesta,
    MedicionCrear,
    MedicionResponse,
)
from app.services import medicion_service

router = APIRouter(prefix="/mediciones", tags=["mediciones"])


# ---------------------------------------------------------
# RF-06 / RF-07: Registrar medición corporal
# ---------------------------------------------------------
@router.post(
    "",
    response_model=MedicionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una nueva medición corporal",
)
def registrar_medicion(
    datos: MedicionCrear,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
) -> MedicionResponse:
    """Registra una medición vinculada al usuario autenticado (RN-60)."""
    try:
        return medicion_service.crear_medicion(db, usuario_actual, datos)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ---------------------------------------------------------
# RF-10: Consulta de inactividad
# ---------------------------------------------------------
@router.get(
    "/inactividad",
    response_model=InactividadRespuesta,
    summary="Consulta la alerta de inactividad de mediciones",
)
def consultar_inactividad(
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
) -> InactividadRespuesta:
    """Retorna si el usuario lleva 30 días o más sin registrar mediciones."""
    return medicion_service.obtener_estado_inactividad(db, usuario_actual)


# ---------------------------------------------------------
# RF-08: Historial de mediciones del usuario
# ---------------------------------------------------------
@router.get(
    "",
    response_model=list[MedicionResponse],
    summary="Historial de mediciones del usuario autenticado",
)
def historial_mediciones(
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
    desde: date | None = Query(
        default=None,
        description="Fecha mínima inclusive (`YYYY-MM-DD`). Filtra por la fecha de la medición.",
    ),
    hasta: date | None = Query(
        default=None,
        description="Fecha máxima inclusive (`YYYY-MM-DD`).",
    ),
) -> list[MedicionResponse]:
    """Obtiene el historial en orden cronológico."""
    if desde is not None and hasta is not None and desde > hasta:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="`desde` no puede ser posterior a `hasta`.",
        )
    return medicion_service.listar_mediciones(db, usuario=usuario, desde=desde, hasta=hasta)


# ---------------------------------------------------------
# RF-08: Detalle de una medición
# ---------------------------------------------------------
@router.get(
    "/{medicion_id}",
    response_model=MedicionResponse,
    summary="Una medición del usuario autenticado por su id",
    responses={404: {"description": "No existe o no es del usuario autenticado"}},
)
def detalle_medicion(
    medicion_id: UUID,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MedicionResponse:
    """Devuelve el detalle de una medición por ID."""
    medicion = medicion_service.obtener_medicion(db, usuario=usuario, medicion_id=medicion_id)
    if medicion is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medición no encontrada.",
        )
    return medicion