"""Catálogo de ejercicios (RF-12) y último registro por ejercicio (RF-20).

RN-38: solo lectura para el usuario final. Este módulo no expone ninguna
función de alta, edición o baja de ejercicios: solo consulta.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entrenamiento import Ejercicio, SerieSesion, Sesion
from app.models.usuario import Usuario
from app.schemas.ejercicio import UltimoRegistroResponse


class EjercicioNoEncontradoError(Exception):
    """El `ejercicio_id` no existe en la tabla de ejercicios. -> 404."""


def _normalizar_filtro(valor: str | None) -> str | None:
    """Trata un filtro presente pero vacío (`?grupo_muscular=`) como "sin
    filtro" (None), en vez de filtrar por la cadena vacía literal (GYM-179).
    """
    if valor is None:
        return None
    valor = valor.strip()
    return valor or None


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

    grupo_muscular = _normalizar_filtro(grupo_muscular)
    equipo = _normalizar_filtro(equipo)
    categoria = _normalizar_filtro(categoria)

    if grupo_muscular is not None:
        consulta = consulta.where(Ejercicio.grupo_muscular == grupo_muscular.lower())
    if equipo is not None:
        consulta = consulta.where(Ejercicio.equipo == equipo.lower())
    if categoria is not None:
        consulta = consulta.where(Ejercicio.categoria == categoria.lower())

    # Orden estable y útil para maquetar: por grupo muscular y luego por nombre.
    consulta = consulta.order_by(Ejercicio.grupo_muscular, Ejercicio.nombre_es)

    return list(db.execute(consulta).scalars().all())


# ---------------------------------------------------------
# RF-20: Último registro del usuario en un ejercicio
# ---------------------------------------------------------
def obtener_ultimo_registro(
    db: Session, *, usuario: Usuario, ejercicio_id: UUID
) -> UltimoRegistroResponse | None:
    """Última serie del usuario en `ejercicio_id`, o `None` si nunca lo hizo.

    Es la base de la sugerencia de progresión: "la última vez hiciste X kg × Y".

    Raises:
        EjercicioNoEncontradoError: el ejercicio no existe.
    """
    # RN-39: solo se comprueba que exista; NO se filtra por `activo`. Un ejercicio
    # desactivado sigue siendo válido en sesiones y conserva su historial.
    existe = db.execute(select(Ejercicio.id).where(Ejercicio.id == ejercicio_id)).first()
    if existe is None:
        raise EjercicioNoEncontradoError

    # Una sola consulta: la sesión más reciente que tenga el ejercicio y, dentro de
    # ella, la serie de mayor `numero_serie`. `series_sesion` no tiene marca de
    # tiempo propia, así que "última" se deriva de la sesión y del número de serie.
    fila = db.execute(
        select(SerieSesion, Sesion.iniciada_en)
        .join(Sesion, Sesion.id == SerieSesion.sesion_id)
        .where(
            SerieSesion.ejercicio_id == ejercicio_id,
            Sesion.usuario_id == usuario.id,  # RN-60: solo sesiones del dueño
            Sesion.finalizada_en.is_not(None),  # la sesión activa no cuenta
        )
        .order_by(  # RN-50: cualquier sesión pasada, no solo la de la misma rutina
            Sesion.iniciada_en.desc(),
            Sesion.id.desc(),
            SerieSesion.numero_serie.desc(),
        )
        .limit(1)
    ).first()
    if fila is None:
        return None

    serie, iniciada_en = fila
    return UltimoRegistroResponse(
        ejercicio_id=serie.ejercicio_id,
        sesion_id=serie.sesion_id,
        fecha=iniciada_en,
        numero_serie=serie.numero_serie,
        repeticiones_realizadas=serie.repeticiones_realizadas,
        peso_usado_kg=serie.peso_usado_kg,
    )
