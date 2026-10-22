"""Servicio del módulo de sesiones de entrenamiento (RF-15, RF-17, RF-18, RF-19)."""

from datetime import date, datetime, time, timedelta, timezone
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.entrenamiento import Ejercicio, Rutina, SerieSesion, Sesion
from app.models.usuario import Usuario
from app.schemas.sesion import (
    CalificacionCrear,
    CalificacionResponse,
    EjercicioHistorial,
    SerieHistorial,
    SesionDetalle,
    SesionFinalizar,
    SesionHistorialItem,
    SesionIniciar,
)

# Margen para relojes de celular algo adelantados: una hora "futura" de hasta
# 5 minutos se acepta; más que eso es un dato erróneo.
_TOLERANCIA_RELOJ = timedelta(minutes=5)

# RF-19: los filtros `desde`/`hasta` son días calendario de Colombia. El nombre
# de la zona resuelve gracias al paquete `tzdata` (requirements.txt); Colombia
# no tiene horario de verano, así que el desfase es siempre -05:00.
_ZONA_COLOMBIA = ZoneInfo("America/Bogota")

# RF-19: texto de `rutina_nombre` cuando la sesión no parte de una rutina
# (entrenamiento libre, o rutina borrada: RN-43).
_NOMBRE_ENTRENAMIENTO_LIBRE = "Entrenamiento libre"


# ---------------------------------------------------------
# Excepciones de dominio (el router las traduce a HTTP)
# ---------------------------------------------------------
class SesionNoEncontradaError(Exception):
    """No existe o es de otro usuario (RN-60). -> 404."""


class RutinaNoEncontradaError(Exception):
    """`rutina_id` no existe o es de otro usuario (RN-60). -> 404."""


class SesionActivaExistenteError(Exception):
    """RN-44: el usuario ya tiene una sesión sin finalizar. -> 409."""

    def __init__(self, sesion_activa: Sesion) -> None:
        super().__init__(sesion_activa.id)
        self.sesion_activa = sesion_activa


class IdempotencyKeyEnUsoError(Exception):
    """La clave ya la usó otra cuenta. -> 409."""


class SesionYaFinalizadaError(Exception):
    """RN-47: no se finaliza (ni se descarta) una sesión ya finalizada. -> 409."""


class SesionSinSeriesError(Exception):
    """RN-69: finalizar sin series requiere `confirmar_sin_series`. -> 409."""


class FechaSesionInvalidaError(Exception):
    """Hora de inicio o fin futura, o fin anterior al inicio. -> 422."""


# ---------------------------------------------------------
# RF-15: Iniciar sesión de entrenamiento
# ---------------------------------------------------------
def _por_idempotency_key(db: Session, clave: str) -> Sesion | None:
    return db.execute(
        select(Sesion).where(Sesion.idempotency_key == clave)
    ).scalar_one_or_none()


def obtener_sesion_activa(db: Session, *, usuario: Usuario) -> Sesion | None:
    """RN-68: la sesión sin finalizar del usuario, si la hay (para reanudarla)."""
    return db.execute(
        select(Sesion).where(
            Sesion.usuario_id == usuario.id,
            Sesion.finalizada_en.is_(None),
        )
    ).scalar_one_or_none()


def iniciar_sesion(
    db: Session, *, usuario: Usuario, datos: SesionIniciar
) -> tuple[Sesion, bool]:
    """Crea la sesión activa. Devuelve `(sesion, creada)`.

    `creada` es `False` cuando es un reintento con la misma `idempotency_key`
    (RN-67): se devuelve la sesión que ya existía, sin crear otra.

    Raises:
        IdempotencyKeyEnUsoError: la clave pertenece a otra cuenta.
        RutinaNoEncontradaError: `rutina_id` no existe o no es del usuario.
        SesionActivaExistenteError: ya hay una sesión sin finalizar (RN-44).
        FechaSesionInvalidaError: `iniciada_en` es futura.
    """
    # RN-67: el reintento se reconoce antes que cualquier otra regla; si no, un
    # reintento chocaría con RN-44 contra la sesión que él mismo creó.
    existente = _por_idempotency_key(db, datos.idempotency_key)
    if existente is not None:
        if existente.usuario_id != usuario.id:
            raise IdempotencyKeyEnUsoError
        return existente, False

    ahora = datetime.now(timezone.utc)
    iniciada_en = datos.iniciada_en or ahora
    if iniciada_en > ahora + _TOLERANCIA_RELOJ:
        raise FechaSesionInvalidaError("La hora de inicio no puede ser futura.")

    if datos.rutina_id is not None:
        rutina = db.execute(
            select(Rutina).where(
                Rutina.id == datos.rutina_id,
                Rutina.usuario_id == usuario.id,  # RN-60
            )
        ).scalar_one_or_none()
        if rutina is None:
            raise RutinaNoEncontradaError

    activa = obtener_sesion_activa(db, usuario=usuario)
    if activa is not None:
        raise SesionActivaExistenteError(activa)  # RN-44

    sesion = Sesion(
        usuario_id=usuario.id,
        rutina_id=datos.rutina_id,
        idempotency_key=datos.idempotency_key,
        iniciada_en=iniciada_en,
    )
    db.add(sesion)
    try:
        db.commit()
    except IntegrityError:
        # Dos reintentos simultáneos con la misma clave: el segundo choca con
        # la restricción única y devuelve la sesión que creó el primero.
        db.rollback()
        existente = _por_idempotency_key(db, datos.idempotency_key)
        if existente is None:
            raise
        if existente.usuario_id != usuario.id:
            raise IdempotencyKeyEnUsoError
        return existente, False
    db.refresh(sesion)
    return sesion, True


# ---------------------------------------------------------
# RF-17: Finalizar sesión / RN-68: descartar sesión activa
# ---------------------------------------------------------
def _sesion_propia(db: Session, *, usuario: Usuario, sesion_id: UUID) -> Sesion:
    sesion = db.execute(
        select(Sesion).where(
            Sesion.id == sesion_id,
            Sesion.usuario_id == usuario.id,  # RN-60
        )
    ).scalar_one_or_none()
    if sesion is None:
        raise SesionNoEncontradaError
    return sesion


def finalizar_sesion(
    db: Session, *, usuario: Usuario, sesion_id: UUID, datos: SesionFinalizar
) -> Sesion:
    """Cierra la sesión y calcula `duracion_segundos` (RN-47).

    RN-67: si dos dispositivos cierran la misma sesión, el primero gana y el
    segundo recibe `SesionYaFinalizadaError`.

    Raises:
        SesionNoEncontradaError, SesionYaFinalizadaError,
        FechaSesionInvalidaError, SesionSinSeriesError.
    """
    sesion = _sesion_propia(db, usuario=usuario, sesion_id=sesion_id)
    if sesion.finalizada_en is not None:
        raise SesionYaFinalizadaError

    ahora = datetime.now(timezone.utc)
    finalizada_en = datos.finalizada_en or ahora
    if finalizada_en > ahora + _TOLERANCIA_RELOJ:
        raise FechaSesionInvalidaError("La hora de fin no puede ser futura.")
    if finalizada_en < sesion.iniciada_en:
        raise FechaSesionInvalidaError("La hora de fin no puede ser anterior a la de inicio.")

    # RN-69: se puede guardar vacía, pero solo si el usuario lo confirmó.
    if not datos.confirmar_sin_series:
        series = db.execute(
            select(func.count()).select_from(SerieSesion).where(SerieSesion.sesion_id == sesion.id)
        ).scalar_one()
        if series == 0:
            raise SesionSinSeriesError

    sesion.finalizada_en = finalizada_en
    sesion.duracion_segundos = int((finalizada_en - sesion.iniciada_en).total_seconds())  # RN-47
    db.commit()
    db.refresh(sesion)
    return sesion


def descartar_sesion(db: Session, *, usuario: Usuario, sesion_id: UUID) -> None:
    """RN-68: elimina una sesión activa y, en cascada, sus series.

    Raises:
        SesionNoEncontradaError, SesionYaFinalizadaError (una sesión finalizada
        es historial: no se descarta).
    """
    sesion = _sesion_propia(db, usuario=usuario, sesion_id=sesion_id)
    if sesion.finalizada_en is not None:
        raise SesionYaFinalizadaError
    # `series_sesion.sesion_id` tiene ON DELETE CASCADE en la base.
    db.execute(delete(Sesion).where(Sesion.id == sesion.id))
    db.commit()


# ---------------------------------------------------------
# RF-18: Calificar el entrenamiento
# ---------------------------------------------------------

def calificar_sesion(
    db: Session,
    *,
    usuario: Usuario,
    sesion_id: UUID,
    datos: CalificacionCrear,
) -> CalificacionResponse | None:
    """Asigna o actualiza la calificación de una sesión finalizada.

    Reglas de negocio:
    - La sesión debe pertenecer al usuario autenticado; de lo contrario se
      devuelve ``None`` (el endpoint traduce a 404).
    - La sesión debe estar finalizada (``finalizada_en IS NOT NULL``); si no,
      se lanza ``ValueError`` (el endpoint traduce a 409 Conflict).
    - Si la sesión ya tenía calificación, se sobreescribe (criterio de
      edición/corrección).

    Returns:
        ``CalificacionResponse`` con los datos actualizados, o ``None`` si la
        sesión no existe o no pertenece al usuario.

    Raises:
        ValueError: si la sesión existe pero aún no ha sido finalizada.
    """
    fila = db.execute(
        select(Sesion).where(
            Sesion.id == sesion_id,
            Sesion.usuario_id == usuario.id,
        )
    ).scalar_one_or_none()

    if fila is None:
        return None

    # RN: solo se puede calificar una sesión ya finalizada.
    if fila.finalizada_en is None:
        raise ValueError(
            "La sesión debe estar finalizada para poder calificarla."
        )

    # Asignar / sobrescribir calificación y nota.
    fila.calificacion = datos.calificacion
    fila.nota = datos.nota

    db.commit()
    db.refresh(fila)

    return CalificacionResponse.model_validate(fila)


# ---------------------------------------------------------
# RF-19: Historial de entrenamientos
# ---------------------------------------------------------
def _inicio_del_dia_bogota(dia: date) -> datetime:
    """Medianoche (00:00) de `dia` en Bogotá, como instante con zona horaria."""
    return datetime.combine(dia, time.min, tzinfo=_ZONA_COLOMBIA)


def _historial_base():
    """SELECT común del historial: sesión + nombre de la rutina.

    LEFT JOIN: RN-43, una sesión sin rutina (libre o rutina borrada) aparece
    igual. El nombre llega en la misma consulta, sin N+1.
    """
    nombre = func.coalesce(Rutina.nombre, _NOMBRE_ENTRENAMIENTO_LIBRE).label("rutina_nombre")
    return select(Sesion, nombre).outerjoin(Rutina, Rutina.id == Sesion.rutina_id)


def _a_item(sesion: Sesion, rutina_nombre: str) -> dict:
    return {
        "id": sesion.id,
        "iniciada_en": sesion.iniciada_en,
        "finalizada_en": sesion.finalizada_en,
        "duracion_segundos": sesion.duracion_segundos,  # RN-47: ya viene calculada
        "rutina_id": sesion.rutina_id,
        "rutina_nombre": rutina_nombre,
        "calificacion": sesion.calificacion,
    }


def listar_historial(
    db: Session,
    *,
    usuario: Usuario,
    limit: int,
    offset: int,
    desde: date | None = None,
    hasta: date | None = None,
) -> list[SesionHistorialItem]:
    """Sesiones finalizadas del usuario, de la más reciente a la más antigua."""
    consulta = _historial_base().where(
        Sesion.usuario_id == usuario.id,  # RN-60
        Sesion.finalizada_en.is_not(None),  # solo finalizadas; la activa va en /activa
    )
    # `desde`/`hasta` son días de Bogotá, inclusivos: [desde 00:00, hasta+1 00:00).
    if desde is not None:
        consulta = consulta.where(Sesion.iniciada_en >= _inicio_del_dia_bogota(desde))
    if hasta is not None:
        consulta = consulta.where(
            Sesion.iniciada_en < _inicio_del_dia_bogota(hasta + timedelta(days=1))
        )
    # RN-49: más reciente primero; `id` desempata para que la paginación sea estable.
    consulta = consulta.order_by(Sesion.iniciada_en.desc(), Sesion.id.desc())
    filas = db.execute(consulta.limit(limit).offset(offset)).all()
    return [SesionHistorialItem(**_a_item(sesion, nombre)) for sesion, nombre in filas]


def obtener_detalle_historial(
    db: Session, *, usuario: Usuario, sesion_id: UUID
) -> SesionDetalle:
    """Detalle de una sesión finalizada propia, con las series agrupadas por ejercicio.

    Raises:
        SesionNoEncontradaError: no existe, es de otro usuario (RN-60) o sigue
            activa (se consulta en `/sesiones/activa`).
    """
    fila = db.execute(
        _historial_base().where(
            Sesion.id == sesion_id,
            Sesion.usuario_id == usuario.id,  # RN-60
            Sesion.finalizada_en.is_not(None),
        )
    ).one_or_none()
    if fila is None:
        raise SesionNoEncontradaError
    sesion, rutina_nombre = fila

    # RN-39: no se filtra por `Ejercicio.activo`; uno desactivado sigue válido en sesiones.
    series = db.execute(
        select(SerieSesion, Ejercicio)
        .join(Ejercicio, Ejercicio.id == SerieSesion.ejercicio_id)
        .where(SerieSesion.sesion_id == sesion.id)
        .order_by(SerieSesion.orden, SerieSesion.numero_serie)
    ).all()

    # Los ejercicios salen en orden de aparición (por `orden`); dentro de cada uno,
    # las series por `numero_serie`.
    grupos: dict[UUID, EjercicioHistorial] = {}
    for serie, ejercicio in series:
        grupo = grupos.get(ejercicio.id)
        if grupo is None:
            grupo = grupos[ejercicio.id] = EjercicioHistorial(
                ejercicio_id=ejercicio.id,
                nombre_es=ejercicio.nombre_es,
                nombre_en=ejercicio.nombre_en,
                series=[],
            )
        grupo.series.append(SerieHistorial.model_validate(serie))
    for grupo in grupos.values():
        grupo.series.sort(key=lambda s: s.numero_serie)

    return SesionDetalle(
        **_a_item(sesion, rutina_nombre),
        nota=sesion.nota,
        ejercicios=list(grupos.values()),
    )
