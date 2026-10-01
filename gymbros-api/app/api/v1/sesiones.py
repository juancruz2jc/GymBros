"""Endpoints para sesiones de entrenamiento (RF-18)."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.usuario import Usuario
from app.schemas.sesion import CalificacionCrear, CalificacionResponse
from app.services import sesion_service

router = APIRouter(prefix="/sesiones", tags=["sesiones"])


# ---------------------------------------------------------
# RF-18: Calificar el entrenamiento
# ---------------------------------------------------------
@router.patch(
    "/{sesion_id}/calificacion",
    response_model=CalificacionResponse,
    summary="Calificar una sesión de entrenamiento finalizada",
    responses={
        404: {"description": "Sesión no encontrada o no pertenece al usuario"},
        409: {"description": "La sesión aún no ha sido finalizada"},
        422: {"description": "Datos de calificación inválidos"},
    },
)
def calificar_sesion(
    sesion_id: UUID,
    datos: CalificacionCrear,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
) -> CalificacionResponse:
    """Asigna o actualiza la calificación de una sesión finalizada (RF-18).

    - **404**: la sesión no existe o pertenece a otro usuario.
    - **409**: la sesión existe pero aún no ha sido finalizada.
    - **422**: la calificación no es un entero entre 1 y 5, o se envió un
      booleano en el campo numérico.

    Se permite corregir la calificación: si la sesión ya estaba calificada,
    los nuevos valores reemplazan a los anteriores.
    """
    try:
        resultado = sesion_service.calificar_sesion(
            db, usuario=usuario_actual, sesion_id=sesion_id, datos=datos,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    if resultado is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sesión no encontrada.",
        )

    return resultado
