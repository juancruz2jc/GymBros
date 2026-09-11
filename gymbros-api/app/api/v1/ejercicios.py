"""Endpoints del catálogo de ejercicios (RF-12)."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.ejercicio import EjercicioResponse
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
