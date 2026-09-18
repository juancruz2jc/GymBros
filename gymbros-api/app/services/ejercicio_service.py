"""Catálogo de ejercicios (RF-12): consulta de solo lectura.

RN-38: solo lectura para el usuario final. Este módulo no expone ninguna
función de alta, edición o baja de ejercicios: solo consulta.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entrenamiento import Ejercicio


def listar_catalogo(
    db: Session,
    *,
    grupo_muscular: str | None = None,
    equipo: str | None = None,
    categoria: str | None = None,
) -> list[Ejercicio]:
    """Lista los ejercicios del catálogo público, con filtros opcionales.

    RN-39: el catálogo/búsqueda pública solo muestra ejercicios con
    `activo = True`. Un ejercicio desactivado sigue siendo válido si ya está
    referenciado desde una rutina o sesión, pero eso se resuelve consultándolo
    por su relación (rutina_ejercicios / series_sesion), nunca por este
    listado. Por eso el filtro `activo == True` vive aquí, en el servicio de
    catálogo, y en ningún otro sitio.

    Los filtros son coincidencia exacta sobre los valores del catálogo
    (`snake_case`, en minúsculas). Se normaliza la entrada (trim + minúsculas)
    para tolerar `?grupo_muscular=Pecho` desde el cliente.
    """
    consulta = select(Ejercicio).where(Ejercicio.activo.is_(True))  # RN-39

    if grupo_muscular is not None:
        consulta = consulta.where(
            Ejercicio.grupo_muscular == grupo_muscular.strip().lower()
        )
    if equipo is not None:
        consulta = consulta.where(Ejercicio.equipo == equipo.strip().lower())
    if categoria is not None:
        consulta = consulta.where(Ejercicio.categoria == categoria.strip().lower())

    # Orden estable y útil para maquetar: por grupo muscular y luego por nombre.
    consulta = consulta.order_by(Ejercicio.grupo_muscular, Ejercicio.nombre_es)

    return list(db.execute(consulta).scalars().all())
