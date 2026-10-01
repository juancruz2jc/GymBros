"""Servicio del módulo de sesiones de entrenamiento (RF-18)."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entrenamiento import Sesion
from app.models.usuario import Usuario
from app.schemas.sesion import CalificacionCrear, CalificacionResponse


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
