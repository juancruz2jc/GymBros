# API · Sesiones de entrenamiento

Estado: **RF-15 (iniciar)** · **RF-16 (registrar series, GYM-16)** ·
**RF-17 (finalizar)** · **RN-68 (descartar / reanudar)** · **RF-18 (calificar)** ·
**RF-19 (historial, GYM-155)** implementados.
Base URL local: `http://localhost:8001` · Prefijo: `/api/v1` · Todos los
endpoints requieren `Authorization: Bearer <access_token>`.

---

## Ciclo de vida de una sesión

```
POST /sesiones ──► ACTIVA ──(POST /sesiones/{id}/series)──► POST /sesiones/{id}/finalizar ──► FINALIZADA ──► PATCH /sesiones/{id}/calificacion
                     │                                                          (opcional, RN-48)
                     └──► DELETE /sesiones/{id}  (descartar, RN-68)
```

- Una sesión está **activa** mientras `finalizada_en` es `null`.
- Cada usuario tiene **como máximo una sesión activa** (RN-44).
- Si la app se cierra sin finalizar ni descartar, la sesión **sigue activa** y
  se recupera con `GET /sesiones/activa` (RN-68).

---

## `POST /api/v1/sesiones` — iniciar (RF-15)

### Cuerpo (`SesionIniciar`)

| Campo | Tipo | Reglas |
|---|---|---|
| `idempotency_key` | string (1–255) | **Obligatorio.** Lo genera la app (p. ej. un UUID) al iniciar la sesión y lo reusa en cada reintento (RN-67). |
| `rutina_id` | UUID \| `null` | Opcional. Rutina **propia** de la que parte la sesión (RN-60). Omitirla es entrenar libre. |
| `iniciada_en` | datetime **con zona horaria** \| `null` | Opcional. Momento real de inicio, para sesiones iniciadas sin conexión (RNF-02). Si se omite, la hora del servidor. Sin zona horaria → `422`. |

### Respuestas

| Código | Cuándo | Cuerpo |
|---|---|---|
| `201 Created` | Sesión creada. | `SesionResponse` |
| `200 OK` | **Reintento** con una `idempotency_key` que ya creó una sesión de este usuario: no se duplica (RN-67). | `SesionResponse` de la sesión existente |
| `404 Not Found` | `rutina_id` no existe o es de otro usuario. | `{ "detail": "Rutina no encontrada." }` |
| `409 Conflict` | Ya hay una sesión activa (RN-44). El detalle incluye su id. | `{ "detail": "Ya tienes una sesión activa (<id>). Finalízala o descártala antes de iniciar otra." }` |
| `409 Conflict` | La `idempotency_key` la usó otra cuenta. | `{ "detail": "La idempotency_key ya está en uso. Genera una nueva." }` |
| `422` | `iniciada_en` futura (más de 5 min de margen), sin zona horaria, o cuerpo inválido. | — |

El reintento se reconoce **antes** que RN-44: si no, un reintento chocaría con
la sesión activa que él mismo creó. Dos reintentos simultáneos con la misma
clave también terminan en la misma sesión (la restricción única de
`idempotency_key` frena al segundo).

### `SesionResponse`

```json
{
  "id": "89fca215-05f5-4d9e-a613-b60e74333459",
  "rutina_id": null,
  "idempotency_key": "7d1c3b0e-…",
  "iniciada_en": "2026-10-07T20:00:00Z",
  "finalizada_en": null,
  "duracion_segundos": null,
  "calificacion": null,
  "nota": null
}
```

---

## `GET /api/v1/sesiones/activa` — reanudar (RN-68)

| Código | Cuándo |
|---|---|
| `200 OK` | `SesionResponse` de la sesión activa. |
| `404 Not Found` | `{ "detail": "No tienes una sesión activa." }` |

---

## `POST /api/v1/sesiones/{sesion_id}/series` — registrar series (RF-16)

Registra una serie o un lote en una sesión **activa**. Pensado para la app
online (serie por serie) y offline (lote al recuperar conexión, RNF-02).

### Cuerpo (`SeriesPayload`)

`{ "series": {…} }` (una) o `{ "series": [{…}, {…}] }` (lote, mínimo 1). Cada
serie (`SerieCrear`):

| Campo | Tipo | Reglas |
|---|---|---|
| `ejercicio_id` | UUID | Debe existir en el catálogo. Uno **desactivado** sí vale (RN-39). |
| `numero_serie` | int | ≥ 1. Número de la serie dentro del ejercicio. |
| `repeticiones_realizadas` | int | **≥ 0**: `0` es una serie fallida, no un error (RN-45). |
| `peso_usado_kg` | number | 0 a 999.99 (`0` vale: peso corporal o fallida, RN-45). |
| `orden` | int | ≥ 1. Posición en la sesión. |

Se rechazan booleanos en los campos numéricos (`true` no se convierte en `1`).

**Idempotente (upsert):** la clave natural es `(sesion_id, ejercicio_id,
numero_serie)` (restricción única de BD-04). Reenviar una serie que ya existe
**la actualiza** en vez de duplicarla: sirve para reintentos offline y para
corregir una serie mal registrada.

### Respuestas

| Código | Cuándo |
|---|---|
| `201 Created` | `list[SerieResponse]`: las series creadas o actualizadas. |
| `404 Not Found` | La sesión no existe o es de otro usuario, **o** algún `ejercicio_id` no existe en el catálogo. |
| `409 Conflict` | La sesión ya está finalizada (RN-46). |
| `422` | Datos inválidos, lote vacío, o **la misma serie dos veces en el mismo lote** (sería ambiguo cuál vale). |

---

## `POST /api/v1/sesiones/{sesion_id}/finalizar` — finalizar (RF-17)

### Cuerpo (`SesionFinalizar`) — opcional, se puede enviar vacío

| Campo | Tipo | Reglas |
|---|---|---|
| `finalizada_en` | datetime con zona horaria \| `null` | Momento real de cierre (RNF-02). Si se omite, la hora del servidor. No puede ser futura ni anterior a `iniciada_en`. |
| `confirmar_sin_series` | bool (default `false`) | RN-69: necesario para guardar una sesión **sin series**. |

`duracion_segundos` = `finalizada_en − iniciada_en`, calculado por el backend
(RN-47); el cliente no lo envía.

### Respuestas

| Código | Cuándo | Cuerpo |
|---|---|---|
| `200 OK` | Finalizada. | `SesionResponse` con `finalizada_en` y `duracion_segundos`. |
| `404 Not Found` | No existe o es de otro usuario (RN-60). | `{ "detail": "Sesión no encontrada." }` |
| `409 Conflict` | Ya estaba finalizada (RN-47). Con dos dispositivos, **gana el primero que cierra** (RN-67). | `{ "detail": "La sesión ya estaba finalizada." }` |
| `409 Conflict` | No tiene series y no se envió `confirmar_sin_series: true` (RN-69). La app debe advertir al usuario y reenviar con la confirmación. | `{ "detail": "La sesión no tiene series registradas. Para guardarla vacía, envía confirmar_sin_series: true." }` |
| `422` | `finalizada_en` futura o anterior al inicio. | — |

---

## `DELETE /api/v1/sesiones/{sesion_id}` — descartar (RN-68)

Borra definitivamente una sesión **activa** y, en cascada
(`ON DELETE CASCADE`), todas sus series.

| Código | Cuándo |
|---|---|
| `204 No Content` | Descartada. |
| `404 Not Found` | No existe o es de otro usuario. |
| `409 Conflict` | Está finalizada: ya es historial y no se descarta. |

---

## `PATCH /api/v1/sesiones/{sesion_id}/calificacion` — calificar (RF-18)

Cuerpo: `calificacion` (entero 1–5, se rechazan booleanos) y `nota` (texto,
opcional). Solo sesiones **finalizadas**; si ya tenía calificación, se
reemplaza. Calificar es opcional (RN-48).

| Código | Cuándo |
|---|---|
| `200 OK` | `{ "id", "calificacion", "nota", "finalizada_en" }` |
| `404 Not Found` | No existe o es de otro usuario. |
| `409 Conflict` | La sesión aún no está finalizada. |
| `422` | `calificacion` fuera de 1–5 o booleana. |

---

## `GET /api/v1/sesiones` — historial (RF-19)

Sesiones **finalizadas** del usuario autenticado, de la más reciente a la más
antigua (RN-49). La sesión activa **no** aparece: se consulta en
`GET /sesiones/activa`.

### Parámetros de query (todos opcionales)

| Parámetro | Tipo | Por defecto | Reglas |
|---|---|---|---|
| `limit` | entero | `20` | De 1 a 100. Fuera de rango o no numérico → `422`. |
| `offset` | entero | `0` | Mínimo 0. Negativo o no numérico → `422`. |
| `desde` | fecha `YYYY-MM-DD` | — | Día mínimo **inclusive**. |
| `hasta` | fecha `YYYY-MM-DD` | — | Día máximo **inclusive**. |

- `desde` y `hasta` se aplican sobre `iniciada_en` y son **días calendario de
  Bogotá** (`America/Bogota`, UTC-5 todo el año). El rango en UTC es
  `[desde 00:00 Bogotá, hasta + 1 día 00:00 Bogotá)`. Una sesión iniciada a las
  9:30 p. m. hora de Bogotá es del día de Bogotá aunque en UTC ya sea el día
  siguiente (`iniciada_en` se devuelve en UTC).
- `desde > hasta` → `422` con el mismo mensaje que `GET /mediciones`.
- Orden fijo: `iniciada_en` descendente y `id` descendente como desempate, así
  paginar no repite ni pierde sesiones.

### Paginación (patrón del proyecto)

Es el primer listado paginado de la API y fija el patrón: `limit` + `offset` como
query params validados por FastAPI (`Query(ge=…, le=…)`), y la respuesta es una
**lista plana**, igual que los demás listados. No hay un total en la respuesta:
el cliente sabe que llegó al final cuando recibe menos de `limit` elementos (o
una lista vacía).

### Respuestas

| Código | Cuándo | Cuerpo |
|---|---|---|
| `200 OK` | Siempre que la petición sea válida; sin sesiones, `[]`. | `list[SesionHistorialItem]` |
| `401` | Token ausente, inválido o expirado. | `{ "detail": "No autenticado." }` |
| `422` | `limit`/`offset` fuera de rango, fecha mal formada o `desde > hasta`. | `{ "detail": "`desde` no puede ser posterior a `hasta`." }` (o el detalle de validación de FastAPI) |

### `SesionHistorialItem`

```json
{
  "id": "20edb0d3-ddf2-4a8f-94fb-410674b4457e",
  "iniciada_en": "2026-10-14T11:00:00Z",
  "finalizada_en": "2026-10-14T11:35:00Z",
  "duracion_segundos": 2100,
  "rutina_id": "32a555e6-5a3e-4cbb-b26d-9c30bd642fe5",
  "rutina_nombre": "Demo · Empuje",
  "calificacion": 5
}
```

- `duracion_segundos` ya viene calculada al finalizar (RN-47).
- `rutina_id` es `null` si se entrenó libre **o si la rutina se eliminó**
  (RN-43); en ambos casos `rutina_nombre` es `"Entrenamiento libre"` y la
  sesión aparece igual.
- `calificacion` es `null` si no se calificó (RN-48).
- El nombre de la rutina sale de un `LEFT JOIN` en la misma consulta: el listado
  es **1 sentencia SQL** sin importar cuántas sesiones devuelva.

### Ejemplos

```bash
# Las 20 más recientes (valores por defecto)
curl -H "Authorization: Bearer $TOKEN" "http://localhost:8001/api/v1/sesiones"

# Segunda página de 10
curl -H "Authorization: Bearer $TOKEN" "http://localhost:8001/api/v1/sesiones?limit=10&offset=10"

# Solo septiembre de 2026 (días de Bogotá, extremos incluidos)
curl -H "Authorization: Bearer $TOKEN" "http://localhost:8001/api/v1/sesiones?desde=2026-09-01&hasta=2026-09-30"

# limit fuera de rango -> 422
curl -i -H "Authorization: Bearer $TOKEN" "http://localhost:8001/api/v1/sesiones?limit=101"
```

---

## `GET /api/v1/sesiones/{sesion_id}` — detalle (RF-19)

Detalle de una sesión **finalizada** propia, con las series agrupadas por
ejercicio. En el router se declara **después** de `GET /sesiones/activa`; si no,
`activa` caería en el UUID y daría `422`.

| Código | Cuándo | Cuerpo |
|---|---|---|
| `200 OK` | Sesión finalizada del usuario. | `SesionDetalle` |
| `401` | Token ausente, inválido o expirado. | `{ "detail": "No autenticado." }` |
| `404 Not Found` | No existe, **es de otro usuario** (RN-60) o **sigue activa**. | `{ "detail": "Sesión no encontrada." }` (el mismo cuerpo en los tres casos) |
| `422` | `sesion_id` no es un UUID. | Detalle de validación de FastAPI. |

### `SesionDetalle`

Los campos de `SesionHistorialItem` más `nota` y `ejercicios`:

```json
{
  "id": "41a6f87b-b5ef-4da1-9ccc-47e1e1084d5a",
  "iniciada_en": "2026-09-27T01:35:00Z",
  "finalizada_en": "2026-09-27T02:19:00Z",
  "duracion_segundos": 2640,
  "rutina_id": "019e24fd-730d-4d0e-b3f5-de24393d8d71",
  "rutina_nombre": "Demo · Tirón y pierna",
  "calificacion": 4,
  "nota": "Buen ritmo, subí peso en la última serie.",
  "ejercicios": [
    {
      "ejercicio_id": "2827c29d-ff2f-4e2a-98a1-fcbf7a12d141",
      "nombre_es": "Hiperextensiones",
      "nombre_en": "Back Extension",
      "series": [
        { "numero_serie": 1, "repeticiones_realizadas": 14, "peso_usado_kg": 15.0 },
        { "numero_serie": 2, "repeticiones_realizadas": 7, "peso_usado_kg": 60.0 }
      ]
    }
  ]
}
```

- Los ejercicios salen en **orden de aparición** según `orden` de la serie; las
  series de cada ejercicio, por `numero_serie`.
- Una sesión finalizada **sin series** responde `200` con `"ejercicios": []`.
- **No se filtra por `activo`** del ejercicio (RN-39): uno desactivado
  del catálogo sigue apareciendo en las sesiones donde se usó.
- `peso_usado_kg` es número (`float`), como en el registro de series y en
  mediciones.
- El detalle son **2 sentencias SQL** (la sesión con su rutina, y las series con
  su ejercicio).

```bash
curl -H "Authorization: Bearer $TOKEN" "http://localhost:8001/api/v1/sesiones/$SESION_ID"
```

---

## Reglas de negocio aplicadas

| Regla | Dónde |
|---|---|
| RN-45 · 0 reps / 0 kg son válidos | `SerieCrear` (`ge=0`) |
| RN-46 · series solo en sesión activa | `serie_service.registrar_series` → 409 |
| RN-44 · una sola sesión activa | `sesion_service.iniciar_sesion` → `SesionActivaExistenteError` → 409 |
| RN-47 · duración automática, no se finaliza dos veces | `finalizar_sesion` |
| RN-48 · calificación opcional | `PATCH …/calificacion` aparte del cierre |
| RN-60 · solo el dueño | todas las consultas filtran `usuario_id` del token en el `WHERE`; ajena = 404, igual que inexistente |
| RN-67 · idempotencia offline | `idempotency_key` (restricción única); reintento → 200 con la misma sesión; primer cierre gana |
| RN-68 · descartar / reanudar | `DELETE /sesiones/{id}` y `GET /sesiones/activa` |
| RN-69 · finalizar vacía con advertencia | `confirmar_sin_series` |
| RN-39 · ejercicio desactivado sigue válido en sesiones | `obtener_detalle_historial` no filtra por `Ejercicio.activo` |
| RN-43 · borrar una rutina no borra sus sesiones (`rutina_id = null`) | `ON DELETE SET NULL` + `LEFT JOIN` en el historial → `"Entrenamiento libre"` |
| RN-47 · `duracion_segundos` calculada | el historial devuelve el valor guardado al finalizar |
| RN-49 · historial de más reciente a más antiguo | `listar_historial`: `iniciada_en DESC, id DESC` |
| RN-60 · solo el dueño; ajena = 404 igual que inexistente | `usuario_id` en el `WHERE` de listado y detalle |

## Pendiente / fuera de este alcance

- **RN-56 (racha y logros al finalizar):** RF-23/RF-24 son del siguiente
  sprint. Cuando se implementen, se evalúan dentro de `finalizar_sesion`.
- **RN-44 con peticiones simultáneas:** ver "Limitaciones" (índice único parcial).
## Limitaciones (mejoras pendientes)

Ninguna requiere cambiar el contrato de la API. Ambas necesitan una migración de
Alembic, que **se coordinará con el equipo** (la base de Supabase es compartida);
no se incluyeron en GYM-155.

- **Índice `(usuario_id, iniciada_en DESC)` en `sesiones`.** Hoy solo existe
  `ix_sesiones_usuario_id`. `GET /sesiones` filtra por usuario y ordena por
  `iniciada_en`, así que con un historial grande la base ordena todas las
  sesiones del usuario en cada página (y `OFFSET` las recorre). Con decenas de
  sesiones no se nota; con cientos o miles sí.
- **Índice único parcial de una sola sesión activa por usuario**
  (`usuario_id WHERE finalizada_en IS NULL`). Hoy RN-44 se valida consultando
  antes de insertar: dos inicios simultáneos con claves distintas podrían crear
  dos sesiones activas.
- **Paginación por `offset`:** si se crea una sesión nueva mientras el cliente
  pagina, una página puede repetir un elemento. Es aceptable para un historial
  que se consulta tras entrenar; si molestara, el paso siguiente sería
  paginación por cursor (`iniciada_en`, `id`).

## Casos de prueba

### RF-19 — historial

Ejecutados el **2026-10-15** contra el stack local (API en docker + PostgreSQL 16
local, migraciones hasta `ce4773f63c25`), con los datos de
`scripts/seed_sesiones_demo.py` (25 sesiones finalizadas, 1 activa, 3 usuarios).
Los casos 15–17 usan la sesión de las 9:30 p. m. hora de Bogotá (en UTC ya es
el día siguiente). En el caso 28 una cuenta nueva creó rutina → sesión y luego
borró la rutina.
**Pasan las 60 comprobaciones** del guion; esta tabla las agrupa.

| # | Caso | Esperado |
|---|---|---|
| 1 | `GET /sesiones` del usuario demo | `200`, 25 sesiones (la 26.ª, activa, no sale) |
| 2 | Orden de la lista | `iniciada_en` descendente |
| 3 | Sin `limit` | 20 elementos, los mismos que `limit=20` |
| 4 | Usuario ajeno | `200`, solo su única sesión; ninguna del demo |
| 5 | `rutina_nombre` con rutina / sin rutina | nombre de la rutina / `"Entrenamiento libre"` (3 sesiones libres) |
| 6 | Item del listado | exactamente 7 campos |
| 7 | `limit=10` con `offset` 0, 10 y 20 | 10 + 10 + 5 = 25, sin repetidas ni faltantes, mismo orden que la lista completa |
| 8 | `offset=30` | `200`, `[]` |
| 9 | `limit=0` / `limit=101` / `offset=-1` / `limit=abc` | `422` cada uno |
| 10 | `limit=1` y `limit=100` | `200` (extremos válidos) |
| 11 | Rango que abarca 11 sesiones (`2026-08-25` a `2026-09-30`) | exactamente esas 11; las sesiones de ambos extremos incluidas; orden descendente |
| 12 | Rango en el futuro | `200`, `[]` |
| 13 | `desde=2026-10-10&hasta=2026-10-01` | `422`, `` `desde` no puede ser posterior a `hasta`. `` |
| 14 | `desde=no-es-fecha` | `422` |
| 15 | `desde=hasta=2026-09-22` (día de Bogotá de la sesión de 9:30 p. m.) | la incluye |
| 16 | `desde=hasta=2026-09-23` (su día en UTC) | no la incluye |
| 17 | `hasta=2026-09-22` / `desde=2026-09-23` | la incluye / la excluye |
| 18 | `GET /sesiones/{id}` propia con series | `200`, 3 ejercicios × 3 series, series por `numero_serie` |
| 19 | Campos del detalle | los 7 del item + `nota` + `ejercicios`; `peso_usado_kg` numérico |
| 20 | Orden de ejercicios | igual al orden de aparición por `orden` de la serie, en las 24 sesiones con series |
| 21 | Sesión finalizada sin series | `200`, `"ejercicios": []` |
| 22 | Sesión con *Hip Adductor Machine* y otra con *Smith Machine Bench Press* (inactivos) | `200`, el ejercicio aparece con sus series; el catálogo público sigue sin listarlos (RN-39) |
| 23 | Detalle de la sesión activa | `404` `"Sesión no encontrada."` |
| 24 | Detalle de una sesión de otro usuario | `404`, mismo cuerpo (RN-60) |
| 25 | Detalle de un UUID inexistente | `404`, mismo cuerpo que 23 y 24 |
| 26 | `sesiones/no-es-uuid` | `422` |
| 27 | Sin token / token inválido (listado y detalle) | `401` |
| 28 | Rutina eliminada tras finalizar la sesión | listado y detalle `200`; `rutina_id = null`, `"Entrenamiento libre"`, series intactas (RN-43) |
| 29 | Usuario sin sesiones | `200`, `[]` |
| 30 | `GET /sesiones/activa` tras añadir `/{id}` | `200`, no cae en el UUID |
| 31 | Sentencias SQL | listado de 25 sesiones: 1; detalle: 2 |

### RF-15, RF-17 y RN-68 — iniciar, finalizar, descartar

Ejecutados contra Supabase el 2026-10-07 con dos usuarios de prueba (borrados
al final). Rutina y series insertadas directo en la base porque rutinas
(GYM-149) y series (GYM-16) aún no estaban en `dev`. **Los 25 pasan.**

### RF-16 — series

Ejecutados contra Supabase el 2026-10-08 con dos usuarios de prueba (borrados
al final). **Los 11 pasan.** Los casos 5–7 fallaban en la versión original de
GYM-16 y se corrigieron al integrarla.

| # | Caso | Esperado |
|---|---|---|
| 1 | Una serie como objeto | `201`, lista de 1 |
| 2 | Lote de 2 | `201`, lista de 2 |
| 3 | Reenviar la misma serie con otros valores | `201`, actualizada |
| 4 | (tras el 3) series en la sesión | 3, no se duplicó |
| 5 | Serie fallida: 0 reps, 0 kg (RN-45) | `201` (antes `422`) |
| 6 | `ejercicio_id` inexistente | `404` (antes `500`) |
| 7 | Lote con la misma serie repetida | `422` (antes `500`) |
| 8 | Booleano en `repeticiones_realizadas` | `422` |
| 9 | Lote vacío | `422` |
| 10 | Usuario B registra en la sesión de A | `404` |
| 11 | Registrar en sesión finalizada (RN-46) | `409` |

| # | Caso | Esperado |
|---|---|---|
| 1 | `GET /activa` sin sesión | `404` |
| 2 | Iniciar libre | `201`, `finalizada_en` y `duracion_segundos` `null` |
| 3 | Reintento con la misma clave | `200`, mismo `id` |
| 4 | Iniciar otra con sesión activa | `409` con el id de la activa |
| 5 | Usuario B usa la clave de A | `409` |
| 6 | `GET /activa` con sesión | `200`, la sesión |
| 7–8 | B finaliza / descarta la sesión de A | `404` |
| 9–11 | Descartar activa con una serie | `204`; serie borrada; `GET /activa` → `404` |
| 12–13 | Iniciar con rutina ajena / inexistente | `404` |
| 14–15 | `iniciada_en` futura / sin zona horaria | `422` |
| 16 | Iniciar con rutina propia, `iniciada_en` hace 2 h | `201` |
| 17 | Finalizar sin series ni confirmación, sin cuerpo | `409` (RN-69) |
| 18–19 | `finalizada_en` antes del inicio / futura | `422` |
| 20 | Finalizar con serie, 1 h después del inicio | `200`, `duracion_segundos = 3600` |
| 21 | Finalizar otra vez | `409` |
| 22 | Descartar sesión finalizada | `409` |
| 23 | Calificar la finalizada | `200` |
| 24 | Iniciar otra tras finalizar | `201` |
| 25 | Finalizar vacía con `confirmar_sin_series: true` | `200` |
