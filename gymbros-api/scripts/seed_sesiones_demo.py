"""Datos de ejemplo del historial de entrenamientos (RF-19 / GYM-155).

Crea usuarios de prueba y 25 sesiones finalizadas de un usuario demo, repartidas
en los últimos ~90 días, para probar ``GET /api/v1/sesiones`` (paginación,
filtro por fechas, orden) y ``GET /api/v1/sesiones/{id}``.

Qué carga
---------
- ``demo.historial@example.com`` / ``Demo12345`` (cumple RN-21): dueño de todo
  lo demás. Con 2 rutinas propias y:
    * 25 sesiones finalizadas, con calificaciones y notas variadas.
    * Casos especiales entre ellas: sesiones sin rutina (``rutina_id`` NULL,
      RN-43), una finalizada **sin series** (RN-69), dos con un ejercicio
      **inactivo** (RN-39) y una a las 9:30 p. m. hora de Bogotá (en UTC ya es
      el día siguiente: borde del filtro ``desde``/``hasta``).
    * 1 sesión **activa** (``finalizada_en`` NULL): no debe salir en el historial.
- ``demo.ajeno@example.com`` / ``Demo12345``: una sesión propia, para probar
  que el usuario demo no la ve (RN-60).
- ``demo.vacio@example.com`` / ``Demo12345``: sin sesiones (lista vacía).

Requisito: el catálogo ya sembrado (``python -m scripts.seed_ejercicios``).

FRENO DE SEGURIDAD
------------------
Este script escribe usuarios y sesiones falsos; nunca debe tocar la base
compartida del equipo (Supabase). ``config.py`` no distingue entornos (no hay
variable de entorno que lo indique), así que el control es sobre la base:

1. Aborta si el host de ``DATABASE_URL`` no es ``localhost``, ``127.0.0.1``,
   ``::1`` o ``db`` (el servicio de la base en docker compose). No hay forma de
   saltarse esta comprobación.
2. Exige ``--confirmar`` y, antes de escribir, imprime el host y la base.

Cómo correrlo
-------------
Desde ``gymbros-api/`` con el venv activado::

    python -m scripts.seed_sesiones_demo --confirmar

Con Docker, desde la raíz del monorepo::

    docker compose exec api python -m scripts.seed_sesiones_demo --confirmar

Es idempotente: cada sesión demo tiene una ``idempotency_key`` fija
(``demo-historial-01`` ...), los usuarios se identifican por correo y las rutinas
por nombre; lo que ya existe se omite. Las fechas se calculan respecto al día de
la primera ejecución. Para empezar de cero hay que borrar los usuarios demo (la
cascada borra todo lo suyo, RN-71).
"""

from __future__ import annotations

import argparse
import random
import sys
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

# Permite además ``python scripts/seed_sesiones_demo.py``: añade la raíz de
# ``gymbros-api/`` al path para poder importar el paquete ``app``.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from sqlalchemy.engine import make_url

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import hashear_password
from app.models.entrenamiento import Ejercicio, Rutina, RutinaEjercicio, SerieSesion, Sesion
from app.models.usuario import Usuario

# Hosts donde se permite escribir: solo máquina local o el servicio `db` de docker.
_HOSTS_PERMITIDOS = {"localhost", "127.0.0.1", "::1", "db"}

_ZONA_COLOMBIA = ZoneInfo("America/Bogota")

_PASSWORD_DEMO = "Demo12345"  # RN-21: 8+ caracteres, con letra y número
_CORREO_DEMO = "demo.historial@example.com"
_CORREO_AJENO = "demo.ajeno@example.com"
_CORREO_VACIO = "demo.vacio@example.com"

_TOTAL_SESIONES = 25
_PREFIJO_KEY = "demo-historial-"
_KEY_ACTIVA = "demo-historial-activa"
_KEY_AJENA = "demo-ajeno-01"

# Posiciones (0-based) de los casos especiales dentro de las 25 sesiones.
_SIN_RUTINA = {4, 11, 18}  # entrenamiento libre, rutina_id NULL
_SIN_SERIES = 9  # finalizada sin series (RN-69)
_INACTIVOS = {14: "Hip Adductor Machine", 19: "Smith Machine Bench Press"}  # RN-39
_NOCHE_BOGOTA = 6  # 9:30 p. m. en Bogotá = día siguiente en UTC

# Rutinas del usuario demo: nombre -> grupos musculares de sus ejercicios.
_RUTINAS = {
    "Demo · Empuje": ("pecho", "hombros", "triceps"),
    "Demo · Tirón y pierna": ("espalda", "biceps", "piernas"),
}

_CALIFICACIONES = [5, 4, None, 3, 5, 4, 2]
_NOTAS = [
    "Buen ritmo, subí peso en la última serie.",
    None,
    "Cansado, dormí poco.",
    "Sesión corta por tiempo.",
    None,
]


def _verificar_base_local() -> None:
    """Aborta (código 2) si `DATABASE_URL` no apunta a una base local."""
    url = make_url(settings.DATABASE_URL)
    host = (url.host or "").lower()
    if host not in _HOSTS_PERMITIDOS:
        print(
            f"ABORTADO: el host de la base es '{host or '(vacío)'}', no es local.\n"
            f"Este script solo corre contra {', '.join(sorted(_HOSTS_PERMITIDOS))}; "
            "nunca contra la base compartida (Supabase).",
            file=sys.stderr,
        )
        sys.exit(2)


def _inicio_local(dia: date, hora: int, minuto: int) -> datetime:
    """Instante (UTC) de `dia` a `hora:minuto` en hora de Bogotá."""
    local = datetime.combine(dia, time(hora, minuto), tzinfo=_ZONA_COLOMBIA)
    return local.astimezone(timezone.utc)


def _usuario(db, correo: str, nombre: str):
    """Devuelve (usuario, creado). Se identifica por correo."""
    existente = db.execute(select(Usuario).where(Usuario.correo == correo)).scalar_one_or_none()
    if existente is not None:
        return existente, False
    ahora = datetime.now(timezone.utc)
    nuevo = Usuario(
        correo=correo,
        hash_password=hashear_password(_PASSWORD_DEMO),
        nombre=nombre,
        consentimiento_datos=True,
        consentimiento_en=ahora,
    )
    db.add(nuevo)
    db.flush()
    return nuevo, True


def _serie(rng: random.Random, sesion_id, ejercicio, numero: int, orden: int):
    return SerieSesion(
        sesion_id=sesion_id,
        ejercicio_id=ejercicio.id,
        numero_serie=numero,
        repeticiones_realizadas=rng.randint(6, 15),
        peso_usado_kg=Decimal(10 + 5 * rng.randint(0, 12)),
        orden=orden,
    )


def _agregar_series(db, sesion, ejercicios, semilla: str) -> int:
    """3 series por ejercicio; `orden` corre a lo largo de toda la sesión."""
    rng = random.Random(semilla)  # determinista: mismos datos en cada base
    orden = 1
    for ejercicio in ejercicios:
        for numero in (1, 2, 3):
            db.add(_serie(rng, sesion.id, ejercicio, numero, orden))
            orden += 1
    return orden - 1


def cargar_sesiones_demo() -> None:
    """Crea usuarios, rutinas y sesiones demo que falten. Idempotente."""
    db = SessionLocal()
    try:
        # --- Catálogo requerido ---
        activos = {}
        for grupo in {g for gs in _RUTINAS.values() for g in gs}:
            ejercicio = db.execute(
                select(Ejercicio)
                .where(Ejercicio.grupo_muscular == grupo, Ejercicio.activo.is_(True))
                .order_by(Ejercicio.nombre_en)
                .limit(1)
            ).scalar_one_or_none()
            activos[grupo] = ejercicio
        inactivos = {
            nombre: db.execute(
                select(Ejercicio).where(Ejercicio.nombre_en == nombre)
            ).scalar_one_or_none()
            for nombre in _INACTIVOS.values()
        }
        if any(e is None for e in activos.values()) or any(e is None for e in inactivos.values()):
            print(
                "ABORTADO: falta el catálogo de ejercicios. Corre primero "
                "`python -m scripts.seed_ejercicios`.",
                file=sys.stderr,
            )
            sys.exit(1)

        # --- Usuarios ---
        demo, demo_nuevo = _usuario(db, _CORREO_DEMO, "Usuario Demo")
        ajeno, ajeno_nuevo = _usuario(db, _CORREO_AJENO, "Usuario Ajeno")
        _, vacio_nuevo = _usuario(db, _CORREO_VACIO, "Usuario Vacío")

        # --- Rutinas del usuario demo (por nombre) ---
        rutinas: dict[str, tuple[Rutina, list]] = {}
        for nombre, grupos in _RUTINAS.items():
            ejercicios = [activos[g] for g in grupos]
            rutina = db.execute(
                select(Rutina).where(Rutina.usuario_id == demo.id, Rutina.nombre == nombre)
            ).scalar_one_or_none()
            if rutina is None:
                rutina = Rutina(usuario_id=demo.id, nombre=nombre, favorita=False)
                db.add(rutina)
                db.flush()
                for orden, ejercicio in enumerate(ejercicios, start=1):
                    db.add(
                        RutinaEjercicio(
                            rutina_id=rutina.id,
                            ejercicio_id=ejercicio.id,
                            orden=orden,
                            series_objetivo=3,
                            repeticiones_objetivo=10,
                            descanso_segundos=90,
                        )
                    )
            rutinas[nombre] = (rutina, ejercicios)
        nombres_rutinas = list(_RUTINAS)
        pool_libre = list(activos.values())

        def existe(clave: str) -> bool:
            return (
                db.execute(select(Sesion.id).where(Sesion.idempotency_key == clave)).first()
                is not None
            )

        creadas = omitidas = 0
        ahora = datetime.now(timezone.utc)
        hoy_bogota = ahora.astimezone(_ZONA_COLOMBIA).date()

        # --- 25 sesiones finalizadas del usuario demo ---
        for i in range(_TOTAL_SESIONES):
            clave = f"{_PREFIJO_KEY}{i + 1:02d}"
            if existe(clave):
                omitidas += 1
                continue

            if i in _SIN_RUTINA:
                rutina, ejercicios = None, [pool_libre[(i + j) % len(pool_libre)] for j in range(3)]
            else:
                rutina, ejercicios = rutinas[nombres_rutinas[i % 2]]
            if i in _INACTIVOS:  # RN-39: un ejercicio inactivo sigue siendo válido en sesiones
                ejercicios = ejercicios[:2] + [inactivos[_INACTIVOS[i]]]

            dia = hoy_bogota - timedelta(days=1 + round(i * 3.6))  # 1 a ~87 días atrás
            if i == _NOCHE_BOGOTA:
                inicio = _inicio_local(dia, 21, 30)
            else:
                inicio = _inicio_local(dia, (6, 7, 12, 18, 19, 20)[i % 6], (i * 7) % 60)
            duracion = timedelta(minutes=35 + (i * 11) % 46)

            sesion = Sesion(
                usuario_id=demo.id,
                rutina_id=rutina.id if rutina is not None else None,
                idempotency_key=clave,
                iniciada_en=inicio,
                finalizada_en=inicio + duracion,
                duracion_segundos=int(duracion.total_seconds()),  # RN-47
                calificacion=_CALIFICACIONES[i % len(_CALIFICACIONES)],
                nota=_NOTAS[i % len(_NOTAS)],
            )
            if i == _SIN_SERIES:
                sesion.calificacion = None
                sesion.nota = "Sesión guardada sin series (RN-69)."
            db.add(sesion)
            db.flush()
            if i != _SIN_SERIES:
                _agregar_series(db, sesion, ejercicios, semilla=clave)
            creadas += 1

        # --- 1 sesión activa del usuario demo (no sale en el historial) ---
        if existe(_KEY_ACTIVA):
            omitidas += 1
        else:
            inicio = ahora - timedelta(minutes=20)
            activa = Sesion(
                usuario_id=demo.id, idempotency_key=_KEY_ACTIVA, iniciada_en=inicio
            )
            db.add(activa)
            db.flush()
            _agregar_series(db, activa, pool_libre[:1], semilla=_KEY_ACTIVA)
            creadas += 1

        # --- 1 sesión del segundo usuario (aislamiento, RN-60) ---
        if existe(_KEY_AJENA):
            omitidas += 1
        else:
            inicio = _inicio_local(hoy_bogota - timedelta(days=2), 18, 0)
            duracion = timedelta(minutes=50)
            sesion = Sesion(
                usuario_id=ajeno.id,
                idempotency_key=_KEY_AJENA,
                iniciada_en=inicio,
                finalizada_en=inicio + duracion,
                duracion_segundos=int(duracion.total_seconds()),
                calificacion=4,
                nota="Sesión de otro usuario.",
            )
            db.add(sesion)
            db.flush()
            _agregar_series(db, sesion, pool_libre[:3], semilla=_KEY_AJENA)
            creadas += 1

        db.commit()
    finally:
        db.close()

    usuarios_nuevos = sum([demo_nuevo, ajeno_nuevo, vacio_nuevo])
    print(
        f"Sesiones demo: {creadas} creadas, {omitidas} ya existían; "
        f"{usuarios_nuevos} usuarios nuevos."
    )
    print(f"Usuario demo: {_CORREO_DEMO} / {_PASSWORD_DEMO}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Carga sesiones de ejemplo para probar el historial (solo bases locales)."
    )
    parser.add_argument(
        "--confirmar",
        action="store_true",
        help="Obligatorio: confirma que quieres escribir usuarios y sesiones de prueba.",
    )
    args = parser.parse_args()

    # El freno va primero: antes de abrir ninguna conexión ni escribir nada.
    _verificar_base_local()
    url = make_url(settings.DATABASE_URL)
    print(f"Base de datos destino: host={url.host} puerto={url.port} base={url.database}")
    if not args.confirmar:
        print("ABORTADO: falta --confirmar. No se escribió nada.", file=sys.stderr)
        sys.exit(2)

    cargar_sesiones_demo()


if __name__ == "__main__":
    main()
