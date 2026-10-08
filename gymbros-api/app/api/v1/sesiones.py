"""Endpoints para sesiones de entrenamiento (RF-15, RF-16, RF-17, RF-18)."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.usuario import Usuario
from app.schemas.serie import SerieResponse, SeriesPayload
from app.schemas.sesion import (
    CalificacionCrear,
    CalificacionResponse,
    SesionFinalizar,
    SesionIniciar,
    SesionResponse,
)
from app.services import sesion_service
from app.services.serie_service import (
    EjercicioNoEncontrado,
    SesionFinalizada,
    SesionNoEncontrada,
    registrar_series,
)

router = APIRouter(prefix="/sesiones", tags=["sesiones"])

_ERROR_NO_ENCONTRADA = "Sesión no encontrada."


# ---------------------------------------------------------
# RF-15: Iniciar sesión de entrenamiento
# ---------------------------------------------------------
@router.post(
    "",
    response_model=SesionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Iniciar una sesión de entrenamiento",
    responses={
        200: {"description": "Reintento con la misma idempotency_key: la sesión ya existía (RN-67)"},
        404: {"description": "La rutina no existe o no es del usuario"},
        409: {"description": "Ya hay una sesión activa (RN-44) o la idempotency_key es de otra cuenta"},
        422: {"description": "Datos inválidos o iniciada_en futura"},
    },
)
def iniciar_sesion(
    datos: SesionIniciar,
    response: Response,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
) -> SesionResponse:
    """Inicia una sesión, a partir de una rutina propia o libre (sin `rutina_id`).

    Reintentar con la misma `idempotency_key` no duplica: responde `200` con la
    sesión ya creada (RN-67).
    """
    try:
        sesion, creada = sesion_service.iniciar_sesion(db, usuario=usuario_actual, datos=datos)
    except sesion_service.IdempotencyKeyEnUsoError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La idempotency_key ya está en uso. Genera una nueva.",
        )
    except sesion_service.RutinaNoEncontradaError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rutina no encontrada.")
    except sesion_service.SesionActivaExistenteError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Ya tienes una sesión activa ({e.sesion_activa.id}). "
                "Finalízala o descártala antes de iniciar otra."
            ),
        )
    except sesion_service.FechaSesionInvalidaError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    if not creada:
        response.status_code = status.HTTP_200_OK
    return sesion


@router.get(
    "/activa",
    response_model=SesionResponse,
    summary="Sesión activa del usuario (para reanudarla)",
    responses={404: {"description": "No hay una sesión activa"}},
)
def sesion_activa(
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
) -> SesionResponse:
    """RN-68: si la app se cerró sin finalizar ni descartar, la sesión sigue
    activa y se reanuda desde aquí."""
    sesion = sesion_service.obtener_sesion_activa(db, usuario=usuario_actual)
    if sesion is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No tienes una sesión activa.",
        )
    return sesion


# ---------------------------------------------------------
# RF-16: Registrar series en una sesión activa
# ---------------------------------------------------------
@router.post(
    "/{sesion_id}/series",
    response_model=list[SerieResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Registrar series en una sesión activa",
    responses={
        404: {"description": "La sesión no existe o no es del usuario, o algún ejercicio no existe"},
        409: {"description": "La sesión ya se encuentra finalizada"},
        422: {"description": "Error de validación en los datos de entrada o serie repetida en el lote"},
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
    except EjercicioNoEncontrado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Algún ejercicio del lote no existe en el catálogo.",
        )
    except SesionFinalizada:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La sesión ya se encuentra finalizada.",
        )


# ---------------------------------------------------------
# RF-17: Finalizar sesión de entrenamiento
# ---------------------------------------------------------
@router.post(
    "/{sesion_id}/finalizar",
    response_model=SesionResponse,
    summary="Finalizar una sesión de entrenamiento",
    responses={
        404: {"description": "Sesión no encontrada o no pertenece al usuario"},
        409: {"description": "Ya estaba finalizada (RN-47) o no tiene series sin confirmar (RN-69)"},
        422: {"description": "finalizada_en futura o anterior al inicio"},
    },
)
def finalizar_sesion(
    sesion_id: UUID,
    datos: SesionFinalizar | None = None,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
) -> SesionResponse:
    """Cierra la sesión; `duracion_segundos` se calcula solo (RN-47).

    Sin series registradas responde `409` salvo que se envíe
    `confirmar_sin_series: true` (RN-69): la app debe advertir al usuario y
    reenviar con la confirmación. Después se califica con
    `PATCH /sesiones/{id}/calificacion` (RF-18, opcional según RN-48).
    """
    try:
        return sesion_service.finalizar_sesion(
            db, usuario=usuario_actual, sesion_id=sesion_id, datos=datos or SesionFinalizar()
        )
    except sesion_service.SesionNoEncontradaError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_ERROR_NO_ENCONTRADA)
    except sesion_service.SesionYaFinalizadaError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La sesión ya estaba finalizada.",
        )
    except sesion_service.SesionSinSeriesError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "La sesión no tiene series registradas. Para guardarla vacía, "
                "envía confirmar_sin_series: true."
            ),
        )
    except sesion_service.FechaSesionInvalidaError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


# ---------------------------------------------------------
# RN-68: Descartar sesión activa
# ---------------------------------------------------------
@router.delete(
    "/{sesion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Descartar una sesión activa (con sus series)",
    responses={
        404: {"description": "Sesión no encontrada o no pertenece al usuario"},
        409: {"description": "La sesión ya está finalizada: es historial y no se descarta"},
    },
)
def descartar_sesion(
    sesion_id: UUID,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
) -> None:
    """Elimina definitivamente una sesión **activa** y todas sus series (RN-68)."""
    try:
        sesion_service.descartar_sesion(db, usuario=usuario_actual, sesion_id=sesion_id)
    except sesion_service.SesionNoEncontradaError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_ERROR_NO_ENCONTRADA)
    except sesion_service.SesionYaFinalizadaError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Una sesión finalizada no se puede descartar.",
        )


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
