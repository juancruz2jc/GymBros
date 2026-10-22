# API · Catálogo de ejercicios

Estado: **RF-12 (catálogo de ejercicios)** implementado · GYM-83 (GYM-138 / GYM-139 / GYM-140) ·
**RF-20 (último registro por ejercicio)** implementado · GYM-156.
Base URL local: `http://localhost:8001` · Prefijo: `/api/v1`

El catálogo es de **solo lectura y público** (RN-38): no hay endpoints para
crear, editar ni borrar ejercicios, y `GET /ejercicios` no exige autenticación.
La única ruta personal de este router es
[`GET /ejercicios/{id}/ultimo-registro`](#get-apiv1ejerciciosidultimo-registro-rf-20),
que sí exige token.

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
- **Un filtro presente pero vacío se trata como ausente** (GYM-179):
  `?grupo_muscular=` es equivalente a no mandar `grupo_muscular`, no a filtrar
  por la cadena vacía. Aplica igual a `equipo` y `categoria`, y a
  combinaciones (`?grupo_muscular=&equipo=mancuerna` filtra solo por
  `equipo`).
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

## `GET /api/v1/ejercicios/{id}/ultimo-registro` (RF-20)

Última serie que **el usuario autenticado** hizo en un ejercicio. Es la base de
la sugerencia de progresión: "la última vez hiciste 70 kg × 6".

### Request

| | |
|---|---|
| Método | `GET` |
| Ruta | `/api/v1/ejercicios/{ejercicio_id}/ultimo-registro` |
| Auth | **Requiere** `Authorization: Bearer <access_token>` (el catálogo, en cambio, sigue siendo público) |
| Cuerpo | No lleva |

| Parámetro | Dónde | Tipo | Descripción |
|---|---|---|---|
| `ejercicio_id` | ruta | UUID | Ejercicio a consultar. Puede estar **desactivado** (RN-39). |

### Cómo se decide "la última serie"

- Solo cuentan las sesiones **finalizadas** del usuario (`finalizada_en IS NOT
  NULL`). La **sesión activa no cuenta**.
- Se toma la sesión finalizada **más reciente** que tenga ese ejercicio
  (`iniciada_en` descendente, `id` descendente como desempate) y, dentro de ella,
  la serie de **mayor `numero_serie`**.
- Cuenta cualquier sesión pasada, no solo las de la misma rutina (RN-50).
- Se resuelve en **una consulta** (`series_sesion` unida a `sesiones`, con
  `ORDER BY … LIMIT 1`); no se traen series a Python.

### Respuestas

| Código | Cuándo | Cuerpo |
|---|---|---|
| `200 OK` | El usuario ya hizo el ejercicio. | `UltimoRegistroResponse` |
| `200 OK` | El usuario **nunca** hizo el ejercicio (no es un error). | `null` |
| `401` | Token ausente, inválido o expirado. | `{ "detail": "No autenticado." }` |
| `404 Not Found` | El `ejercicio_id` no existe en la tabla. | `{ "detail": "Ejercicio no encontrado." }` |
| `422` | `ejercicio_id` no es un UUID. | Detalle de validación de FastAPI. |

Un ejercicio **desactivado** con historial responde `200` con su marca; sin
historial, `200` con `null` (RN-39). El `404` es solo para ids que no están en la
tabla, y se comprueba **antes** que el historial: un id inexistente da `404`
aunque el usuario no tenga datos.

### `UltimoRegistroResponse`

```json
{
  "ejercicio_id": "2827c29d-ff2f-4e2a-98a1-fcbf7a12d141",
  "sesion_id": "a2890915-93ae-4e64-8fc7-368c34c64397",
  "fecha": "2026-10-10T12:07:00Z",
  "numero_serie": 3,
  "repeticiones_realizadas": 6,
  "peso_usado_kg": 70.0
}
```

- `fecha` es el `iniciada_en` de la sesión (UTC).
- `peso_usado_kg` es número (`float`), como en el registro de series y en
  mediciones.
- Una serie fallida (RN-45) es una marca válida: `repeticiones_realizadas = 0`.

### Ejemplos `curl`

```bash
# Última marca en un ejercicio
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8001/api/v1/ejercicios/$EJERCICIO_ID/ultimo-registro"

# Nunca lo hizo -> 200 con el cuerpo: null
# Ejercicio inexistente -> 404 {"detail":"Ejercicio no encontrado."}
# Sin token -> 401 {"detail":"No autenticado."}
```

---

## Reglas de negocio aplicadas

| Regla | Exige | Dónde |
|---|---|---|
| RN-50 | La sugerencia mira la última serie de ese ejercicio en cualquier sesión pasada, no solo en la misma rutina | `obtener_ultimo_registro`: sin filtro por rutina; orden `iniciada_en DESC, id DESC, numero_serie DESC` |
| RN-60 | Todo recurso personal es visible solo para su dueño | `Sesion.usuario_id == usuario.id` en el `WHERE`; el `usuario` sale del token, nunca de la URL |
| RN-38 | El catálogo es de solo lectura para el usuario final: no puede crear ni editar ejercicios | El router `app/api/v1/ejercicios.py` solo declara `GET`; `app/services/ejercicio_service.py` no expone ninguna función de escritura |
| RN-39 | Un ejercicio con `activo = false` no aparece en el catálogo ni en la búsqueda pública; sigue siendo válido si ya está referenciado desde rutinas/sesiones | Filtro `Ejercicio.activo.is_(True)` en `listar_catalogo`. Ese filtro vive **solo** en el servicio de catálogo; las consultas por relación (rutina_ejercicios / series_sesion) no lo aplican. `obtener_ultimo_registro` solo comprueba que el ejercicio **exista**, sin filtrar por `activo` |

---

## Arquitectura (qué hace cada archivo)

| Archivo | Responsabilidad |
|---|---|
| `app/models/entrenamiento.py` | Modelo `Ejercicio` (tabla `ejercicios`): `nombre_es`, `nombre_en`, `grupo_muscular`, `equipo`, `categoria`, `gif_url`, `activo`. Ya existía; RF-12 no añadió columnas. |
| `app/schemas/ejercicio.py` | `EjercicioResponse` (salida del catálogo) y `UltimoRegistroResponse` (RF-20). Sin esquema de entrada: RN-38. |
| `app/services/ejercicio_service.py` | `listar_catalogo(db, *, grupo_muscular, equipo, categoria)`: aplica RN-39 y los filtros. `_normalizar_filtro` trata un filtro vacío (post-`strip()`) como `None` (GYM-179). `obtener_ultimo_registro(db, *, usuario, ejercicio_id)` (RF-20): lanza `EjercicioNoEncontradoError` si el ejercicio no existe y devuelve `None` si el usuario nunca lo hizo. Sin nada de FastAPI. |
| `app/api/v1/ejercicios.py` | Router `/ejercicios`: `GET ""` (público) con los tres filtros como `Query(...)`, y `GET /{ejercicio_id}/ultimo-registro` (con `get_current_user`), que traduce `EjercicioNoEncontradoError` a `404`. |
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
>
> **Casos 9–12 (GYM-179, filtros vacíos) probados en runtime — 2026-09-17.**
> Mismo stack. **Todos pasan** tras el fix en `listar_catalogo`.

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
| 9 | `GET /api/v1/ejercicios?grupo_muscular=` | `200`; **igual que el caso 1** (41 activos) — filtro vacío tratado como ausente (GYM-179). |
| 10 | `GET /api/v1/ejercicios?equipo=` | `200`; igual que el caso 1. |
| 11 | `GET /api/v1/ejercicios?categoria=` | `200`; igual que el caso 1. |
| 12 | `GET /api/v1/ejercicios?grupo_muscular=&equipo=mancuerna` | `200`; **igual que el caso 3** — el filtro vacío se ignora y solo aplica `equipo=mancuerna`. |

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

### RF-20 — último registro (GYM-156)

Ejecutados el **2026-10-15** contra el stack local (API en docker + PostgreSQL 16
local, migraciones en `ce4773f63c25`), con los datos de
`scripts/seed_sesiones_demo.py`: `demo.historial` (25 sesiones finalizadas y 1
activa), `demo.ajeno` (1 finalizada) y `demo.vacio` (sin sesiones). **Pasan los 25
casos.** El valor esperado sale de una consulta SQL **independiente** (subconsultas
con `max()`), no de la misma consulta del servicio.

| # | Caso | Esperado | Obtenido |
|---|---|---|---|
| 1 | Los 8 ejercicios con historial de `demo.historial`, API contra SQL (sesión, `numero_serie`, reps, peso, fecha) | 8/8 coinciden | 8/8 |
| 1 | Lo mismo con `demo.ajeno` | 3/3 coinciden | 3/3 |
| 1b | Back Extension, caso concreto | sesión `a2890915`, serie 3, 6 reps, 70.0 kg | sesión `a2890915`, serie 3, 6 reps, 70.0 kg |
| **2** | **La sesión activa no cuenta** (ver abajo) | La marca de la última finalizada: serie 3, 6 reps, 70.0 kg, sesión `a2890915`; **no** la de la activa (serie 9, 1 rep, 99.5 kg, sesión `bfa2b978`) | serie 3, 6 reps, 70.0 kg, sesión `a2890915` |
| 2b | Precondición: la activa es más reciente que cualquier finalizada | `t` | `t` |
| 3a | `demo.vacio` (sin sesiones), cualquier ejercicio | `200`, `null` | `200`, `null` |
| 3b | `demo.historial` con Ab Wheel Rollout, que nunca hizo | `200`, `null` | `200`, `null` |
| 3c | Cuerpo crudo del `null` | `null`, `application/json` | `null`, `application/json` |
| 4 | Aislamiento con Back Extension, que hicieron ambos | historial: `a2890915`, 70 kg × 6; ajeno: `ffec2614`, 40 kg × 6; sesiones distintas | historial: `a2890915`, 70 kg × 6; ajeno: `ffec2614`, 40 kg × 6 |
| 5a | **Inactivo con historial:** Hip Adductor Machine | `200` con la marca: sesión `5a9e5176`, serie 3, 15 reps, 35.0 kg | `200`, sesión `5a9e5176`, serie 3, 15 reps, 35.0 kg |
| 5a | **Inactivo con historial:** Smith Machine Bench Press | `200` con la marca: sesión `45204254`, serie 3, 15 reps, 55.0 kg | `200`, sesión `45204254`, serie 3, 15 reps, 55.0 kg |
| 5b | Los dos inactivos, con `demo.vacio` (sin historial) | `200`, `null` | `200`, `null` (ambos) |
| 5c | Los dos inactivos siguen fuera del catálogo público | no aparecen | no aparecen |
| 6a | Ejercicio inexistente (UUID válido) | `404` `{"detail": "Ejercicio no encontrado."}` | `404`, mismo cuerpo |
| 6a' | Inexistente, con un usuario sin datos | `404`, mismo cuerpo (existencia antes que historial) | `404`, mismo cuerpo |
| 6b | `ejercicio_id` que no es UUID | `422` | `422` |
| 6c | Sin token | `401` `{"detail": "No autenticado."}` | `401`, mismo cuerpo |
| 6d | Token inválido | `401` | `401` |
| 7a | **Regresión:** `GET /ejercicios` sin token | `200`, 41 activos | `200`, 41 |
| 7b | `?grupo_muscular=pecho` | `200`, 6 | `200`, 6 |
| 7c | `?equipo=barra` | `200`, 8 | `200`, 8 |
| 7d | `?equipo=barra&categoria=compuesto` | `200`, 6 | `200`, 6 |
| 7e | `?grupo_muscular=Pecho` (mayúsculas) | `200`, 6 | `200`, 6 |
| 8 | Sentencias SQL por petición | 1 o 2 | con historial: 2; sin historial: 2; inexistente: 1 |

**Por qué el caso 2 es significativo.** La sesión activa de `demo.historial` es
**más reciente que cualquier finalizada**: si el endpoint la contara, ganaría por
el orden `iniciada_en DESC`. Para que un error saltara a la vista, se añadió a esa
sesión activa una serie 9 del mismo ejercicio (Back Extension) con valores
distintos a los de la última finalizada (1 rep × 99.5 kg frente a 6 reps × 70 kg).
El endpoint siguió devolviendo la marca de la finalizada. Con un fallo en el filtro
`finalizada_en IS NOT NULL` habría devuelto 99.5 kg. Terminada la prueba, esa serie
se borró de la base local.

Las dos consultas son: una comprobación de que el ejercicio existe y un único
`SELECT` de `series_sesion` unida a `sesiones`, ordenado y con `LIMIT 1`.

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

### `ultimo-registro` (RF-20)

6. **`series_sesion` no guarda marca de tiempo propia.** "La última serie" se
   deriva de la sesión (`iniciada_en`, con `id` como desempate) y de
   `numero_serie`; no del momento real en que se registró cada serie. Si una
   sesión se registra en lote o sin conexión (RNF-02), solo se conserva el orden
   por `numero_serie`. Si dos sesiones del usuario tuvieran exactamente el mismo
   `iniciada_en`, gana la de mayor `id`: un desempate estable pero arbitrario.
7. **Sin índice compuesto para esta consulta.** Hoy solo existen índices simples
   sobre `series_sesion.ejercicio_id` y `series_sesion.sesion_id`, y sobre
   `sesiones.usuario_id`. Con un historial grande, un índice compuesto (por
   ejemplo `series_sesion (ejercicio_id, sesion_id)` junto a
   `sesiones (usuario_id, iniciada_en DESC)`) ayudaría a ordenar y limitar sin
   recorrer todas las series del ejercicio. Requiere una migración, que **se
   coordinará con el equipo** (la base de Supabase es compartida); no se incluyó
   en GYM-156.
8. **Solo la última serie.** No devuelve el resto de series de esa sesión ni una
   sugerencia calculada (subir peso o repeticiones): eso lo decide el cliente a
   partir de la marca.
