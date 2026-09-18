"""Endpoints para la gestión de mediciones corporales (RF-06, RF-07, RF-08, RF-10)."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.usuario import Usuario
from app.schemas.medicion import (
    InactividadRespuesta,
    MedicionActualizar,
    MedicionComparativaResponse,
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
# RF-09: Comparación de mediciones por fecha
# ---------------------------------------------------------
@router.get(
    "/comparar",
    response_model=MedicionComparativaResponse,
    summary="Comparar dos mediciones por fecha",
    responses={
        404: {"description": "No se encontraron registros en una o ambas fechas"},
        400: {"description": "Las fechas deben ser distintas"},
    },
)
def comparar_mediciones(
    fecha1: date = Query(..., description="Primera fecha a comparar (`YYYY-MM-DD`)"),
    fecha2: date = Query(..., description="Segunda fecha a comparar (`YYYY-MM-DD`)"),
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MedicionComparativaResponse:
    """Compara dos registros de medición del usuario y calcula sus diferencias."""
    if fecha1 == fecha2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debes ingresar dos fechas distintas para realizar la comparación.",
        )

    resultado = medicion_service.comparar_mediciones(
        db, usuario=usuario, fecha1=fecha1, fecha2=fecha2
    )
    if resultado is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró registro de medición para una o ambas fechas indicadas.",
        )
    return resultado
    
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


# ---------------------------------------------------------
# RN-08 / RN-36 / RN-37: Editar y eliminar medición propia
# ---------------------------------------------------------
@router.put(
    "/{medicion_id}",
    response_model=MedicionResponse,
    summary="Editar una medición del usuario autenticado",
    responses={404: {"description": "No existe o no es del usuario autenticado"}},
)
def editar_medicion(
    medicion_id: UUID,
    datos: MedicionActualizar,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MedicionResponse:
    """Edita los campos indicados de una medición **del usuario del token**.

    Actualización parcial: los campos omitidos no cambian. 404 si el id no existe
    o es de otra persona (RN-08), igual que el GET por id. 422 si algún valor
    sale de los rangos de RN-03 a RN-06. Un `usuario_id` en el cuerpo se ignora,
    nunca reasigna la medición (RN-37).
    """
    medicion = medicion_service.actualizar_medicion(
        db, usuario=usuario, medicion_id=medicion_id, datos=datos
    )
    if medicion is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medición no encontrada.",
        )
    return medicion


@router.delete(
    "/{medicion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una medición del usuario autenticado",
    responses={404: {"description": "No existe o no es del usuario autenticado"}},
)
def borrar_medicion(
    medicion_id: UUID,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Borra definitivamente una medición **del usuario del token** (RN-36).

    404 si el id no existe o es de otra persona (RN-08). Borrar dos veces la
    misma medición: 204 la primera, 404 la segunda.
    """
    if not medicion_service.eliminar_medicion(db, usuario=usuario, medicion_id=medicion_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medición no encontrada.",
        )
