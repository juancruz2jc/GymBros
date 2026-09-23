"""Servicio del módulo de series de sesión (RF-16).

Lógica de negocio para registrar series en una sesión activa del usuario
autenticado, con soporte de upsert para idempotencia (BD-04) y lote
offline (RNF-02).
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entrenamiento import Sesion, SerieSesion
from app.models.usuario import Usuario
from app.schemas.serie import SerieCrear, SerieResponse


# ---------------------------------------------------------
# Excepciones de dominio (desacopladas de HTTP)
# ---------------------------------------------------------
class SesionNoEncontrada(Exception):
    """La sesión no existe o no pertenece al usuario autenticado."""


class SesionFinalizada(Exception):
    """La sesión ya se encuentra finalizada; no admite más series."""


# ---------------------------------------------------------
# RF-16: Registrar series en una sesión activa
# ---------------------------------------------------------
def registrar_series(
    db: Session,
    *,
    usuario: Usuario,
    sesion_id: UUID,
    series: list[SerieCrear],
) -> list[SerieResponse]:
    """Registra (o actualiza por upsert) una o varias series en la sesión.

    Flujo:
    1. Verificar que la sesión existe y pertenece al ``usuario``.
       → ``SesionNoEncontrada`` si no se cumple.
    2. Verificar que la sesión no esté finalizada (``finalizada_en IS NULL``).
       → ``SesionFinalizada`` si ya tiene fecha de fin.
    3. Para cada serie del lote, buscar si ya existe un registro con la
       combinación ``(sesion_id, ejercicio_id, numero_serie)``:
       - Si existe → actualizar ``repeticiones_realizadas``, ``peso_usado_kg``
         y ``orden`` (upsert / idempotencia BD-04).
       - Si no existe → insertar una nueva fila.
    4. Commit y devolver las series resultantes.

    Args:
        db: Sesión de SQLAlchemy.
        usuario: Usuario autenticado (del token).
        sesion_id: ID de la sesión donde se registran las series.
        series: Lista de series a registrar (ya normalizada por el schema).

    Returns:
        Lista de ``SerieResponse`` con los registros creados o actualizados.

    Raises:
        SesionNoEncontrada: La sesión no existe o pertenece a otro usuario.
        SesionFinalizada: La sesión ya está finalizada.
    """
    # 1. Buscar la sesión filtrando por usuario autenticado
    sesion = db.execute(
        select(Sesion).where(
            Sesion.id == sesion_id,
            Sesion.usuario_id == usuario.id,
        )
    ).scalar_one_or_none()

    if sesion is None:
        raise SesionNoEncontrada(
            "La sesión no existe o no pertenece al usuario autenticado."
        )

    # 2. Verificar que la sesión no esté finalizada
    if sesion.finalizada_en is not None:
        raise SesionFinalizada("La sesión ya se encuentra finalizada.")

    # 3. Upsert de cada serie
    resultados: list[SerieSesion] = []

    for dato in series:
        # Buscar registro existente por la clave natural compuesta
        existente = db.execute(
            select(SerieSesion).where(
                SerieSesion.sesion_id == sesion_id,
                SerieSesion.ejercicio_id == dato.ejercicio_id,
                SerieSesion.numero_serie == dato.numero_serie,
            )
        ).scalar_one_or_none()

        if existente is not None:
            # Upsert: actualizar los campos modificables
            existente.repeticiones_realizadas = dato.repeticiones_realizadas
            existente.peso_usado_kg = dato.peso_usado_kg
            existente.orden = dato.orden
            resultados.append(existente)
        else:
            # Insertar nueva serie
            nueva = SerieSesion(
                sesion_id=sesion_id,
                ejercicio_id=dato.ejercicio_id,
                numero_serie=dato.numero_serie,
                repeticiones_realizadas=dato.repeticiones_realizadas,
                peso_usado_kg=dato.peso_usado_kg,
                orden=dato.orden,
            )
            db.add(nueva)
            resultados.append(nueva)

    # 4. Persistir todo el lote en una sola transacción
    db.commit()

    # Refrescar para obtener los IDs generados y valores por defecto
    for fila in resultados:
        db.refresh(fila)

    return [SerieResponse.model_validate(fila) for fila in resultados]
