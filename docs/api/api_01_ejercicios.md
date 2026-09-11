# API · Catálogo de ejercicios

Estado: **RF-12 (catálogo de ejercicios)** implementado · GYM-83 (GYM-138 / GYM-139 / GYM-140).
Base URL local: `http://localhost:8001` · Prefijo: `/api/v1`

El catálogo es de **solo lectura y público** (RN-38): no hay endpoints para
crear, editar ni borrar ejercicios, y no se exige autenticación.

---

## `GET /api/v1/ejercicios`

Lista los ejercicios **activos** del catálogo, con filtros opcionales.

### Request

| | |
|---|---|
| Método | `GET` |
| Ruta | `/api/v1/ejercicios` |
| Auth | No requiere |
| Cuerpo | No lleva |

#### Parámetros de query (todos opcionales)

| Parámetro | Tipo | Descripción |
|---|---|---|
| `grupo_muscular` | string | Coincidencia exacta con el grupo muscular. Ej.: `pecho`, `espalda`, `piernas`, `gluteos`, `hombros`, `biceps`, `triceps`, `core`, `pantorrillas`, `cuerpo_completo`. |
| `equipo` | string | Coincidencia exacta con el equipo. Ej.: `barra`, `mancuerna`, `peso_corporal`, `maquina`, `polea`, `kettlebell`. |
| `categoria` | string | Coincidencia exacta con la categoría. Ej.: `compuesto`, `aislamiento`, `cardio`, `movilidad`, `estiramiento`. |

- Los valores del catálogo son `snake_case` en minúsculas. La entrada se
  normaliza (se recortan espacios y se pasa a minúsculas), así que
  `?grupo_muscular=Pecho` y `?grupo_muscular=pecho` son equivalentes.
- Los filtros se combinan con **AND**. Sin ningún filtro se devuelve el
  catálogo activo completo.
- Un valor que no existe en el catálogo (`?equipo=trineo`) no es un error:
  simplemente devuelve `[]`.
- Orden de salida: por `grupo_muscular` y luego por `nombre_es`.

### Respuestas

#### `200 OK` — lista de ejercicios (`list[EjercicioResponse]`)

```json
[
  {
    "id": "3f7b2c10-1e4a-4c9d-8b21-2a6f9c0d1e34",
    "nombre_es": "Curl de bíceps con barra",
    "nombre_en": "Barbell Biceps Curl",
    "grupo_muscular": "biceps",
    "equipo": "barra",
    "categoria": "aislamiento",
    "gif_url": "https://media.gymbros.app/ejercicios/barbell-biceps-curl.gif"
  }
]
```

| Campo | Descripción |
|---|---|
| `id` | UUID del ejercicio. |
| `nombre_es` / `nombre_en` | Nombre en español / inglés. |
| `grupo_muscular`, `equipo`, `categoria` | Valores del catálogo (`snake_case`). |
| `gif_url` | URL del GIF demostrativo, o `null` si aún no tiene. |

No se devuelve el campo `activo`: este listado solo trae ejercicios activos
(RN-39), así que sería siempre `true`.

#### `422 Unprocessable Entity`

Solo si un parámetro de query llega con un tipo imposible de interpretar como
texto (no ocurre en la práctica con estos tres filtros). No hay 401/403: el
endpoint es público.

### Ejemplos `curl`

```bash
# Catálogo activo completo
curl http://localhost:8001/api/v1/ejercicios

# Un filtro
curl "http://localhost:8001/api/v1/ejercicios?grupo_muscular=espalda"

# Combinación de filtros (AND)
curl "http://localhost:8001/api/v1/ejercicios?grupo_muscular=pecho&equipo=mancuerna"

# Filtro sin resultados -> []
curl "http://localhost:8001/api/v1/ejercicios?categoria=powerlifting"
```

---

## Reglas de negocio aplicadas

| Regla | Exige | Dónde |
|---|---|---|
| RN-38 | El catálogo es de solo lectura para el usuario final: no puede crear ni editar ejercicios | El router `app/api/v1/ejercicios.py` solo declara `GET`; `app/services/ejercicio_service.py` no expone ninguna función de escritura |
| RN-39 | Un ejercicio con `activo = false` no aparece en el catálogo ni en la búsqueda pública; sigue siendo válido si ya está referenciado desde rutinas/sesiones | Filtro `Ejercicio.activo.is_(True)` en `listar_catalogo`. Ese filtro vive **solo** en el servicio de catálogo; las consultas por relación (rutina_ejercicios / series_sesion) no lo aplican |

---

## Arquitectura (qué hace cada archivo)

| Archivo | Responsabilidad |
|---|---|
| `app/models/entrenamiento.py` | Modelo `Ejercicio` (tabla `ejercicios`): `nombre_es`, `nombre_en`, `grupo_muscular`, `equipo`, `categoria`, `gif_url`, `activo`. Ya existía; RF-12 no añadió columnas. |
| `app/schemas/ejercicio.py` | `EjercicioResponse` (salida). Sin esquema de entrada: RN-38. |
| `app/services/ejercicio_service.py` | `listar_catalogo(db, *, grupo_muscular, equipo, categoria)`: aplica RN-39 y los filtros. Sin nada de FastAPI. |
| `app/api/v1/ejercicios.py` | Router `/ejercicios`: `GET ""` con los tres filtros como `Query(...)`. Traduce a `list[EjercicioResponse]`. |
| `app/api/v1/router.py` | Monta `ejercicios.router` bajo `/api/v1`. |
| `scripts/seed_ejercicios.py` | Carga el dataset de maquetado (~40 ejercicios, 2 inactivos para probar RN-39). Se corre a mano. |

Los endpoints se declaran con `def` (no `async def`): el acceso a datos es
síncrono (SQLAlchemy sin driver async); FastAPI los ejecuta en un threadpool.

---

## Casos de prueba (GYM-140)

Mientras no exista la colección Postman base del proyecto (GYM-94/95/96), los
casos quedan documentados aquí. Requisito previo: base migrada
(`alembic upgrade head`) y seed cargado
(`python -m scripts.seed_ejercicios`).

> **Camino feliz probado en runtime — 2026-09-10.** Los 8 casos y la verificación
> de RN-39 se ejecutaron contra el stack de `docker compose` (API en
> `localhost:8001`, PostgreSQL 16, migraciones en `444873b25785`, seed idempotente
> con 43 filas: 41 activas + 2 inactivas). **Todos pasan.**

| # | Petición | Resultado esperado |
|---|---|---|
| 1 | `GET /api/v1/ejercicios` | `200`; lista con **todos los activos** del seed (los 2 inactivos **no** salen). |
| 2 | `GET /api/v1/ejercicios?grupo_muscular=pecho` | `200`; solo ejercicios de `pecho`, todos activos. |
| 3 | `GET /api/v1/ejercicios?equipo=mancuerna` | `200`; solo ejercicios con `equipo = mancuerna`. |
| 4 | `GET /api/v1/ejercicios?categoria=cardio` | `200`; solo `categoria = cardio` (`Burpee`, `Jump Rope`). |
| 5 | `GET /api/v1/ejercicios?grupo_muscular=pecho&equipo=mancuerna` | `200`; intersección (AND): solo pecho + mancuerna. |
| 6 | `GET /api/v1/ejercicios?grupo_muscular=Pecho` | `200`; **igual que el caso 2** (la entrada se normaliza a minúsculas). |
| 7 | `GET /api/v1/ejercicios?categoria=powerlifting` | `200` con cuerpo `[]` (valor inexistente, no es error). |
| 8 | `GET /api/v1/ejercicios?grupo_muscular=piernas` | `200`; el ejercicio inactivo `Hip Adductor Machine` (grupo `piernas`) **no** aparece → verifica RN-39. |

### Verificación de RN-39 en Swagger

1. `http://localhost:8001/docs` → `GET /api/v1/ejercicios` → *Try it out* → *Execute* sin filtros.
2. Confirmar que `Hip Adductor Machine` y `Smith Machine Bench Press` **no** están en la respuesta.
3. En `psql`: `UPDATE ejercicios SET activo = true WHERE nombre_en = 'Hip Adductor Machine';`
4. Repetir la petición: ahora **sí** aparece. Revertir con `activo = false`.

**Resultado (2026-09-10):** sin filtros → `200` con 41 activos y ninguno de los 2
inactivos (`Hip Adductor Machine`, `Smith Machine Bench Press`), verificados como
presentes en la tabla. Tras poner `activo = true` en `Hip Adductor Machine` el
listado pasa a 42 y el ejercicio aparece en `?grupo_muscular=piernas` (7 → 8); al
revertir vuelve a 41. La normalización de entrada
(`?grupo_muscular=%20Pecho%20`, `?equipo=MANCUERNA`) devuelve exactamente lo mismo
que el valor canónico. `GET /openapi.json`: el endpoint no declara `security`
(público, RN-38) y los 3 filtros figuran como `required: false`.

---

## Limitaciones conocidas / en el radar

1. **Dataset de maquetado, no definitivo.** El seed cubre 43 ejercicios (41
   activos + 2 inactivos) para poder probar los filtros. RF-12 prevé partir de un dataset tipo
   ExerciseGymGifsDB y migrar a una fuente con licencia clara (wger). Las
   `gif_url` actuales son marcadores de posición y algunas filas van con
   `gif_url = null`.
2. **Sin paginación.** El catálogo completo se devuelve de una vez. Con el
   dataset definitivo (cientos de ejercicios) habrá que añadir `limit`/`offset`
   o cursor.
3. **Sin búsqueda por texto.** Solo filtros exactos por los tres campos. Buscar
   por nombre (`?q=press`) queda para una iteración posterior.
4. **Filtros de valor único.** No se puede pedir `?grupo_muscular=pecho,espalda`
   en una sola llamada.
5. **Sin tests automatizados** (pytest no se ha visto en el curso); la
   verificación es la tabla de casos de arriba, ejecutada a mano el 2026-09-10
   contra el stack de `docker compose`. La colección Postman llegará con
   GYM-94/95/96.
