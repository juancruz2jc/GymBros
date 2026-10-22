"""Carga inicial del catálogo de ejercicios (RF-12 / GYM-138).

Dataset de maquetado: un conjunto representativo de ejercicios comunes,
repartido entre varios grupos musculares, equipos y categorías, para poder
probar los filtros de ``GET /api/v1/ejercicios``. No es el catálogo
definitivo: la especificación de RF-12 parte de un dataset tipo
ExerciseGymGifsDB y prevé migrar a una fuente con licencia clara (wger) más
adelante. Las ``gif_url`` de aquí son marcadores de posición.

RN-38: el catálogo es de solo lectura para el usuario final; no puede crear ni
editar ejercicios. Este seed es una tarea administrativa que se corre a mano,
no una operación expuesta por la API.

RN-39: se cargan a propósito dos ejercicios con ``activo = False``. El endpoint
público de catálogo debe ocultarlos; sirven para comprobar ese filtro.

Cómo correrlo
-------------
Desde ``gymbros-api/`` con el venv activado::

    python -m scripts.seed_ejercicios

Con Docker, desde la raíz del monorepo::

    docker compose exec api python -m scripts.seed_ejercicios

Es idempotente: identifica cada ejercicio por ``nombre_en`` y solo inserta los
que faltan, así que se puede volver a correr sin duplicar filas.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Permite además ``python scripts/seed_ejercicios.py``: añade la raíz de
# ``gymbros-api/`` al path para poder importar el paquete ``app``.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.entrenamiento import Ejercicio

# Base para las gif_url de maquetado. Se sustituye por la fuente con licencia
# (wger) cuando se cargue el catálogo definitivo.
_BASE_GIF = "https://media.gymbros.app/ejercicios"

# Ejercicios sin GIF todavía (movilidad y estiramientos, sobre todo). Se
# guardan con gif_url = NULL, que la columna admite.
_SIN_GIF = {
    "Cat-Cow",
    "Standing Hamstring Stretch",
}

# (nombre_es, nombre_en, grupo_muscular, equipo, categoria, activo)
#
# Taxonomías usadas (todo en español, snake_case):
#   grupo_muscular: pecho, espalda, piernas, gluteos, hombros, biceps,
#                   triceps, core, pantorrillas, cuerpo_completo
#   equipo:         barra, mancuerna, peso_corporal, maquina, polea,
#                   kettlebell
#   categoria:      compuesto, aislamiento, cardio, movilidad, estiramiento
_EJERCICIOS: list[tuple[str, str, str, str, str, bool]] = [
    # --- Pecho ---
    ("Press de banca con barra", "Barbell Bench Press", "pecho", "barra", "compuesto", True),
    ("Press inclinado con mancuernas", "Incline Dumbbell Bench Press", "pecho", "mancuerna", "compuesto", True),
    ("Aperturas con mancuernas", "Dumbbell Fly", "pecho", "mancuerna", "aislamiento", True),
    ("Fondos en paralelas", "Parallel Bar Dips", "pecho", "peso_corporal", "compuesto", True),
    ("Cruce de poleas", "Cable Crossover", "pecho", "polea", "aislamiento", True),
    ("Flexiones de pecho", "Push-Up", "pecho", "peso_corporal", "compuesto", True),
    # --- Espalda ---
    ("Dominadas", "Pull-Up", "espalda", "peso_corporal", "compuesto", True),
    ("Remo con barra", "Barbell Bent-Over Row", "espalda", "barra", "compuesto", True),
    ("Remo con mancuerna a una mano", "One-Arm Dumbbell Row", "espalda", "mancuerna", "compuesto", True),
    ("Jalón al pecho en polea", "Lat Pulldown", "espalda", "polea", "compuesto", True),
    ("Remo sentado en polea", "Seated Cable Row", "espalda", "polea", "compuesto", True),
    ("Peso muerto convencional", "Conventional Deadlift", "espalda", "barra", "compuesto", True),
    ("Hiperextensiones", "Back Extension", "espalda", "peso_corporal", "aislamiento", True),
    # --- Piernas ---
    ("Sentadilla con barra", "Barbell Back Squat", "piernas", "barra", "compuesto", True),
    ("Prensa de piernas", "Leg Press", "piernas", "maquina", "compuesto", True),
    ("Zancadas con mancuernas", "Dumbbell Walking Lunge", "piernas", "mancuerna", "compuesto", True),
    ("Sentadilla búlgara", "Bulgarian Split Squat", "piernas", "mancuerna", "compuesto", True),
    ("Extensión de cuádriceps", "Leg Extension", "piernas", "maquina", "aislamiento", True),
    ("Curl femoral tumbado", "Lying Leg Curl", "piernas", "maquina", "aislamiento", True),
    ("Estiramiento de isquiotibiales de pie", "Standing Hamstring Stretch", "piernas", "peso_corporal", "estiramiento", True),
    # --- Glúteos ---
    ("Puente de glúteos con barra", "Barbell Hip Thrust", "gluteos", "barra", "compuesto", True),
    ("Patada de glúteo en polea", "Cable Glute Kickback", "gluteos", "polea", "aislamiento", True),
    # --- Hombros ---
    ("Press militar con barra", "Standing Barbell Overhead Press", "hombros", "barra", "compuesto", True),
    ("Elevaciones laterales con mancuernas", "Dumbbell Lateral Raise", "hombros", "mancuerna", "aislamiento", True),
    ("Pájaros con mancuernas", "Bent-Over Reverse Fly", "hombros", "mancuerna", "aislamiento", True),
    ("Face pull en polea", "Cable Face Pull", "hombros", "polea", "aislamiento", True),
    # --- Bíceps ---
    ("Curl de bíceps con barra", "Barbell Biceps Curl", "biceps", "barra", "aislamiento", True),
    ("Curl alterno con mancuernas", "Alternating Dumbbell Curl", "biceps", "mancuerna", "aislamiento", True),
    ("Curl martillo", "Hammer Curl", "biceps", "mancuerna", "aislamiento", True),
    # --- Tríceps ---
    ("Extensión de tríceps en polea", "Cable Triceps Pushdown", "triceps", "polea", "aislamiento", True),
    ("Press francés con barra", "Lying Barbell Triceps Extension", "triceps", "barra", "aislamiento", True),
    ("Fondos de tríceps en banco", "Bench Triceps Dip", "triceps", "peso_corporal", "compuesto", True),
    # --- Core ---
    ("Plancha abdominal", "Front Plank", "core", "peso_corporal", "aislamiento", True),
    ("Elevación de piernas colgado", "Hanging Leg Raise", "core", "peso_corporal", "aislamiento", True),
    ("Crunch en polea", "Cable Crunch", "core", "polea", "aislamiento", True),
    ("Rueda abdominal", "Ab Wheel Rollout", "core", "peso_corporal", "aislamiento", True),
    ("Gato-camello", "Cat-Cow", "core", "peso_corporal", "movilidad", True),
    # --- Pantorrillas ---
    ("Elevación de talones de pie", "Standing Calf Raise", "pantorrillas", "maquina", "aislamiento", True),
    # --- Cuerpo completo ---
    ("Swing con kettlebell", "Kettlebell Swing", "cuerpo_completo", "kettlebell", "compuesto", True),
    ("Burpee", "Burpee", "cuerpo_completo", "peso_corporal", "cardio", True),
    ("Saltos a la cuerda", "Jump Rope", "cuerpo_completo", "peso_corporal", "cardio", True),
    # --- Inactivos (RN-39): no deben aparecer en el catálogo público ---
    ("Máquina de aductores (retirada)", "Hip Adductor Machine", "piernas", "maquina", "aislamiento", False),
    ("Press de banca en Smith (variante antigua)", "Smith Machine Bench Press", "pecho", "maquina", "compuesto", False),
]


def _gif_url(nombre_en: str) -> str | None:
    """URL de maquetado a partir del nombre en inglés, o ``None`` si no hay GIF."""
    if nombre_en in _SIN_GIF:
        return None
    slug = re.sub(r"[^a-z0-9]+", "-", nombre_en.lower()).strip("-")
    return f"{_BASE_GIF}/{slug}.gif"


def cargar_ejercicios() -> None:
    """Inserta los ejercicios que falten. Idempotente por ``nombre_en``."""
    creados = 0
    omitidos = 0
    sesion = SessionLocal()
    try:
        for nombre_es, nombre_en, grupo_muscular, equipo, categoria, activo in _EJERCICIOS:
            ya_existe = sesion.execute(
                select(Ejercicio.id).where(Ejercicio.nombre_en == nombre_en)
            ).scalar_one_or_none()
            if ya_existe is not None:
                omitidos += 1
                continue
            sesion.add(
                Ejercicio(
                    nombre_es=nombre_es,
                    nombre_en=nombre_en,
                    grupo_muscular=grupo_muscular,
                    equipo=equipo,
                    categoria=categoria,
                    gif_url=_gif_url(nombre_en),
                    activo=activo,
                )
            )
            creados += 1
        sesion.commit()
    finally:
        sesion.close()

    print(
        f"Catálogo de ejercicios: {creados} creados, "
        f"{omitidos} ya existían (total en el dataset: {len(_EJERCICIOS)})."
    )


if __name__ == "__main__":
    cargar_ejercicios()
