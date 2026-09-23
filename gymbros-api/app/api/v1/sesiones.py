"""Endpoints para la gestión de sesiones de entrenamiento (RF-16).

RF-16: Registrar series de la sesión activa — permite registrar una sola serie
o un lote (lista) en la misma petición, con soporte offline (RNF-02) y
manejo idempotente de duplicados (BD-04).
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.usuario import Usuario
from app.schemas.serie import SerieResponse, SeriesPayload
from app.services.serie_service import (
    SesionFinalizada,
    SesionNoEncontrada,
    registrar_series,
)

router = APIRouter(prefix="/sesiones", tags=["sesiones"])


# ---------------------------------------------------------
# RF-16: Registrar series en una sesión activa
# ---------------------------------------------------------
@router.post(
    "/{sesion_id}/series",
    response_model=list[SerieResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Registrar series en una sesión activa",
    responses={
        404: {"description": "La sesión no existe o no pertenece al usuario autenticado"},
        409: {"description": "La sesión ya se encuentra finalizada"},
        422: {"description": "Error de validación en los datos de entrada"},
    },
)
def registrar_series_sesion(
    sesion_id: UUID,
    payload: SeriesPayload,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
) -> list[SerieResponse]:
    """Registra una o varias series en la sesión indicada (RF-16).

    **Comportamiento**:
    - Acepta un objeto ``{ "series": {...} }`` (una serie) o
      ``{ "series": [{...}, {...}] }`` (un lote).
    - Si la combinación ``(sesion_id, ejercicio_id, numero_serie)`` ya existe,
      se actualiza el registro existente (upsert / idempotencia BD-04) en
      lugar de fallar, retornando 201 con el registro actualizado.

    **Errores controlados**:
    - ``404 Not Found``: la sesión no existe o pertenece a otro usuario.
    - ``409 Conflict``: la sesión ya fue finalizada.
    - ``422 Unprocessable Entity``: datos de entrada inválidos (validación
      Pydantic: booleanos en campos numéricos, valores fuera de rango, etc.).
    """
    try:
        return registrar_series(
            db,
            usuario=usuario_actual,
            sesion_id=sesion_id,
            series=payload.series,
        )
    except SesionNoEncontrada:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La sesión no existe o no pertenece al usuario autenticado.",
        )
    except SesionFinalizada:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La sesión ya se encuentra finalizada.",
        )
