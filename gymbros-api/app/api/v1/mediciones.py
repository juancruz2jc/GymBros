"""Endpoints del historial de mediciones (RF-08)."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.usuario import Usuario
from app.schemas.medicion import MedicionActualizar, MedicionResponse
from app.services.medicion_service import (
    actualizar_medicion,
    eliminar_medicion,
    listar_mediciones,
    obtener_medicion,
)

router = APIRouter(prefix="/mediciones", tags=["mediciones"])


# `def`, no `async def`: el acceso a datos es síncrono (ver main.py).
# Protegido: `Depends(get_current_user)` -> 401 sin un access token válido.
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
    """Mediciones del usuario **del token**, en orden cronológico.

    El historial es siempre el del usuario autenticado: no hay parámetro de
    usuario en la ruta ni en el cuerpo (RF-08). Orden por fecha de la medición,
    ascendente (RN-34), no por fecha de registro. `desde`/`hasta` son opcionales
    e inclusivos; sin ellos se devuelve el historial completo. Cada medición
    trae su `imc` calculado (RN-12), o `null` si el usuario no tiene altura
    registrada (RN-09).
    """
    if desde is not None and hasta is not None and desde > hasta:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="`desde` no puede ser posterior a `hasta`.",
        )
    return listar_mediciones(db, usuario=usuario, desde=desde, hasta=hasta)


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
    """Devuelve una medición **del usuario del token** por su id.

    404 si el id no existe **o** es de otra persona: la respuesta es la misma en
    ambos casos, no se confirma ni se niega que el id exista (no filtrar
    información → 404, nunca 403). Un `medicion_id` que no sea un UUID válido lo
    rechaza FastAPI con 422.
    """
    medicion = obtener_medicion(db, usuario=usuario, medicion_id=medicion_id)
    if medicion is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medición no encontrada.",
        )
    return medicion


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
    medicion = actualizar_medicion(
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
    if not eliminar_medicion(db, usuario=usuario, medicion_id=medicion_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medición no encontrada.",
        )
