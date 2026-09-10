<<<<<<< HEAD
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
=======
"""Endpoints del historial de mediciones (RF-08)."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.usuario import Usuario
from app.schemas.medicion import MedicionResponse
from app.services.medicion_service import listar_mediciones, obtener_medicion

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
>>>>>>> origin/feature/GYM-79-historial-mediciones
