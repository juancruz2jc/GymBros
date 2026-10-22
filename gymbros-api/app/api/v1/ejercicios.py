"""Endpoints de ejercicios: catálogo público (RF-12) y último registro (RF-20)."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.usuario import Usuario
from app.schemas.ejercicio import EjercicioResponse, UltimoRegistroResponse
from app.services import ejercicio_service
from app.services.ejercicio_service import listar_catalogo

# RN-38: catálogo de solo lectura -> este router solo declara GET, nunca
# POST/PUT/DELETE de ejercicios.
router = APIRouter(prefix="/ejercicios", tags=["ejercicios"])


# `def`, no `async def`: el acceso a datos es síncrono (ver main.py).
# Sin `Depends` de autenticación: el catálogo es público (RN-38).
@router.get(
    "",
    response_model=list[EjercicioResponse],
    summary="Listar el catálogo de ejercicios",
)
def listar_ejercicios(
    db: Session = Depends(get_db),
    grupo_muscular: str | None = Query(
        default=None,
        description="Filtra por grupo muscular (p. ej. `pecho`, `espalda`, `piernas`).",
    ),
    equipo: str | None = Query(
        default=None,
        description="Filtra por equipo (p. ej. `barra`, `mancuerna`, `peso_corporal`).",
    ),
    categoria: str | None = Query(
        default=None,
        description="Filtra por categoría (p. ej. `compuesto`, `aislamiento`, `cardio`).",
    ),
) -> list[EjercicioResponse]:
    """Devuelve los ejercicios **activos** del catálogo (RN-39).

    Los tres filtros son opcionales y se combinan con AND. Sin filtros devuelve
    el catálogo activo completo. Un ejercicio con `activo = false` nunca aparece
    aquí (RN-39). No requiere autenticación: el catálogo es de solo lectura y
    público (RN-38).
    """
    return listar_catalogo(
        db,
        grupo_muscular=grupo_muscular,
        equipo=equipo,
        categoria=categoria,
    )


# RF-20. A diferencia del catálogo, esta ruta es PERSONAL: exige token y solo ve las
# sesiones del usuario (RN-60). El resto del router sigue siendo público.
@router.get(
    "/{ejercicio_id}/ultimo-registro",
    response_model=UltimoRegistroResponse | None,
    summary="Última serie del usuario en un ejercicio (sugerencia de progresión)",
    responses={
        200: {"description": "La última serie, o `null` si el usuario nunca hizo el ejercicio"},
        401: {"description": "No autenticado"},
        404: {"description": "El ejercicio no existe"},
        422: {"description": "`ejercicio_id` no es un UUID"},
    },
)
def ultimo_registro(
    ejercicio_id: UUID,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
) -> UltimoRegistroResponse | None:
    """Última serie del usuario en este ejercicio, en cualquier sesión finalizada (RN-50).

    Nunca haberlo hecho no es un error: responde `200` con cuerpo `null`. Un
    ejercicio desactivado con historial también responde (RN-39).
    """
    try:
        return ejercicio_service.obtener_ultimo_registro(
            db, usuario=usuario_actual, ejercicio_id=ejercicio_id
        )
    except ejercicio_service.EjercicioNoEncontradoError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ejercicio no encontrado.")
