# API · Rutinas — favoritas (RF-22)

Estado: **RF-22 (marcar rutina como favorita)** implementado · GYM-157.
Base URL local: `http://localhost:8001` · Prefijo: `/api/v1` · Todos los
endpoints requieren `Authorization: Bearer <access_token>`.

> **Alcance de este documento.** Documenta **solo** lo de RF-22: el `PATCH
> /rutinas/{id}/favorita` y el filtro `GET /rutinas?favoritas=true`. Los demás
> endpoints del router de rutinas (RF-13 crear, RF-14 eliminar, RF-21 duplicar,
> y el detalle y la edición) **todavía no están documentados** y corresponden a
> su autor; aquí solo se mencionan cuando hace falta para entender RF-22.

---

## `PATCH /api/v1/rutinas/{rutina_id}/favorita` — alternar favorita (RF-22)

Alterna la rutina entre **favorita** y **no favorita**: si no lo era, la marca;
si lo era, la desmarca (RN-64). No lleva cuerpo.

### Request

| | |
|---|---|
| Método | `PATCH` |
| Ruta | `/api/v1/rutinas/{rutina_id}/favorita` |
| Auth | **Requiere** token |
| Cuerpo | No lleva |

| Parámetro | Dónde | Tipo | Descripción |
|---|---|---|---|
| `rutina_id` | ruta | UUID | Rutina **propia** a alternar. |

### Cómo funciona

- Es **un solo `UPDATE` atómico** (`favorita = NOT favorita`) filtrado por `id` **y**
  `usuario_id` en el `WHERE`. No lee, invierte en Python y guarda: un doble toque
  no puede leer el mismo valor dos veces y dejar el estado incierto; cada toque
  alterna el valor guardado.
- Si el `UPDATE` no afecta ninguna fila (la rutina no existe **o es de otro
  usuario**), responde `404`: ajena e inexistente son indistinguibles (RN-60).
- **No hay límite** de favoritas por usuario (RN-64).
- **No valida los ejercicios de la rutina** (RN-39): una rutina que contiene un
  ejercicio desactivado se puede marcar y desmarcar sin problema.
- Efecto en `actualizado_en`: ver [Limitaciones](#limitaciones-y-hallazgos).

### Respuestas

| Código | Cuándo | Cuerpo |
|---|---|---|
| `200 OK` | Alternada. | `RutinaResponse` con el nuevo valor de `favorita` (`true` o `false`) |
| `401` | Token ausente, inválido o expirado. | `{ "detail": "No autenticado." }` |
| `404 Not Found` | La rutina no existe **o es de otro usuario**. | `{ "detail": "Rutina no encontrada o no tienes permisos" }` (el mismo cuerpo en los dos casos) |
| `422` | `rutina_id` no es un UUID. | Detalle de validación de FastAPI. |

### `RutinaResponse`

Es el mismo esquema que ya devuelven `GET /rutinas/{id}` y `PUT /rutinas/{id}`;
GYM-157 no creó ninguno nuevo.

```json
{
  "id": "32a555e6-5a3e-4cbb-b26d-9c30bd642fe5",
  "usuario_id": "e9201f9e-92c5-4e58-8681-d7240f8e3d07",
  "nombre": "Demo · Empuje",
  "favorita": true,
  "creado_en": "2026-10-16T03:11:19.211923Z",
  "actualizado_en": "2026-10-16T04:16:21.464048Z",
  "ejercicios": [
    {
      "id": "aee35e23-8b23-49a1-ad26-2c940e8695aa",
      "rutina_id": "32a555e6-5a3e-4cbb-b26d-9c30bd642fe5",
      "ejercicio_id": "ae784aa1-4370-4914-8554-527b8925e0a3",
      "orden": 1,
      "series_objetivo": 3,
      "repeticiones_objetivo": 10,
      "descanso_segundos": 90
    }
  ]
}
```

(El ejemplo muestra solo 1 de los 3 ejercicios de la rutina.)

### Ejemplos `curl`

```bash
# Marcar o desmarcar (alterna)
curl -X PATCH -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8001/api/v1/rutinas/$RUTINA_ID/favorita"

# Rutina ajena o inexistente -> 404 {"detail":"Rutina no encontrada o no tienes permisos"}
# Sin token -> 401 {"detail":"No autenticado."}
```

---

## `GET /api/v1/rutinas?favoritas=true` — filtrar favoritas (RF-22)

`GET /rutinas` lista las rutinas del usuario. El parámetro `favoritas` es nuevo y
**opcional**.

| Parámetro | Tipo | Por defecto | Efecto |
|---|---|---|---|
| `favoritas` | booleano | `false` | `true`: solo las rutinas marcadas como favoritas. `false` o ausente: **todas** (el comportamiento de siempre). |

- El orden no cambia: `creado_en` descendente.
- Sin ninguna favorita, `?favoritas=true` responde `200` con `[]` (no es un error).
- Cada item del listado ya incluía `favorita` (es `RutinaResponse`); no hubo
  que cambiar el esquema.

### Valores aceptados de `favoritas`

Es un booleano estándar de FastAPI: se aceptan `true`/`false` en cualquier
combinación de mayúsculas, y también `1`/`0` y sus variantes (`yes`/`no`,
`on`/`off`, `t`/`f`, `y`/`n`; todas verificadas con `200`). Un valor **vacío** (`?favoritas=`) o **no booleano** (`abc`, `2`,
`si`) responde **`422`**.

> **La app debe mandar siempre `true` o `false`.** Esto **difiere** del filtrado
> de `GET /ejercicios` (ver `api_01_ejercicios.md`), donde un filtro vacío
> (`?grupo_muscular=`) se trata como ausente. Aquí un `?favoritas=` vacío **no** es
> "sin filtro": es un `422`.

### Respuestas

| Código | Cuándo | Cuerpo |
|---|---|---|
| `200 OK` | Siempre que el valor sea válido; sin resultados, `[]`. | `list[RutinaResponse]` |
| `401` | Token ausente, inválido o expirado. | `{ "detail": "No autenticado." }` |
| `422` | `favoritas` vacío o no booleano. | Detalle de validación de FastAPI. |

Solo se listan las rutinas **del usuario autenticado**: el filtro de dueño va en
el `WHERE` (RN-60), también con `favoritas=true`.

### Ejemplos `curl`

```bash
# Todas las rutinas (igual que antes)
curl -H "Authorization: Bearer $TOKEN" "http://localhost:8001/api/v1/rutinas"

# Solo las favoritas
curl -H "Authorization: Bearer $TOKEN" "http://localhost:8001/api/v1/rutinas?favoritas=true"

# Valor no booleano -> 422
curl -i -H "Authorization: Bearer $TOKEN" "http://localhost:8001/api/v1/rutinas?favoritas=abc"
```

---

## Reglas de negocio aplicadas

| Regla | Exige | Dónde |
|---|---|---|
| RN-64 | Una rutina se puede marcar y desmarcar como favorita, sin límite | `rutina_service.alternar_favorita`: `favorita = NOT favorita`; no cuenta ni limita favoritas |
| RN-61 | Solo el dueño de una rutina puede modificarla | `Rutina.usuario_id == usuario_id` en el `WHERE` del `UPDATE` |
| RN-60 | Un recurso personal es visible solo para su dueño; un id ajeno da 404, no 403 | `usuario_id` (del token) en el `WHERE`; ajena = inexistente = el mismo 404 |
| RN-39 | Un ejercicio desactivado sigue siendo válido en rutinas ya creadas | `alternar_favorita` **no** llama a `validar_ejercicios_entrada` |

---

## Casos de prueba

Ejecutados el **2026-10-15** contra el stack local (API en docker + PostgreSQL 16
local, migraciones en `ce4773f63c25`), con los datos de
`scripts/seed_sesiones_demo.py`: `demo.historial` (2 rutinas, ambas no
favoritas), `demo.ajeno` y `demo.vacio` (sin rutinas). **Pasan los 45 casos.**
Los valores de la base se comprobaron con consultas SQL independientes. Al
terminar, los datos demo quedaron exactamente como estaban (ver caso 11).

| # | Caso | Esperado | Obtenido |
|---|---|---|---|
| 1 | **Marcar:** PATCH sobre Empuje (`favorita=false`) | `200`, `favorita=true`; en la base `t` | `200`, `true`; base `t` |
| 1b | Forma de la respuesta | `RutinaResponse` completa, con 3 ejercicios | los 7 campos, 3 ejercicios |
| 1c | `actualizado_en` al alternar | antes `NULL`, ahora con fecha | `NULL` → `2026-10-16T04:16:21Z` |
| 2 | **Desmarcar:** PATCH de nuevo | `200`, `favorita=false`; base `f` | `200`, `false`; base `f` |
| 2b | 3.º y 4.º toque | `true` y luego `false` | `true` y `false`; base `f` |
| 3a | `?favoritas=true` sin ninguna marcada | `200`, `[]` | `200`, `[]` |
| 3b | `?favoritas=true` con solo Empuje marcada | solo Empuje | `[Demo · Empuje]` |
| 3c | `?favoritas=true` con las 2 marcadas | las 2, en el orden de siempre | Empuje y Tirón y pierna |
| 3d | Desmarcar una de las 2 | queda solo la otra | `[Demo · Tirón y pierna]` |
| 4a | `GET /rutinas` sin parámetro | `200`, las 2, mismo orden | las 2, mismo orden |
| 4b | `?favoritas=false` | idéntico a 4a | idéntico |
| 4c | `favorita` en cada item del listado | presente | `[false, true]` |
| 5 | `?favoritas=abc`, `2`, vacío, `si` | `422` | `422` en los 4 |
| 5b | `?favoritas=1`, `True`, `TRUE`, `false`, `0` | `200` | `200` en los 5 |
| 6 | **Rutina de otro usuario** (token de `demo.ajeno`) | `404` con el mismo cuerpo que una inexistente; la base no cambia | `404` `{"detail": "Rutina no encontrada o no tienes permisos"}`, idéntico al de la inexistente; base sin cambios (`f` y mismo `actualizado_en` antes y después) |
| 7a | Rutina inexistente (token del dueño) | `404`, mismo cuerpo | `404`, mismo cuerpo |
| 7b | `rutina_id` que no es UUID | `422` | `422` |
| 7c | Sin token | `401` `{"detail": "No autenticado."}` | `401`, mismo cuerpo |
| 7d | Token inválido | `401` | `401` |
| 7e | Usuario sin rutinas sobre una rutina ajena | `404`, mismo cuerpo | `404`, mismo cuerpo |
| 7f | Nada cambió tras los intentos fallidos | `favorita = f` | `f` |
| 8 | **Sin límite (RN-64):** 6 rutinas creadas + las 2 demo, todas favoritas a la vez | todas `true`; `?favoritas=true` devuelve 8 | 6 `true`; 8 devueltas |
| 8b | Confirmación en la base | 8 favoritas | 8 |
| 8c | Limpieza: las 6 creadas borradas | 2 rutinas, no favoritas | 2, `[false, false]` |
| **9** | **RN-39:** PATCH con *Barbell Bench Press* **desactivado** en la base (ejercicio de Empuje) | `200`, `favorita=true` | `200`, `true` |
| 9b | Desmarcar con el ejercicio aún inactivo | `200`, `false` | `200`, `false` |
| 9c | *Observación, no es de GYM-157:* `PUT /rutinas/{id}` con la lista de ejercicios (incluye el inactivo) | `422` | `422` `"El ejercicio Press de banca con barra está inactivo"` |
| 9d | `PUT /rutinas/{id}` solo con `favorita` (sin ejercicios), con el ejercicio inactivo | `200` | `200` |
| 9e | **Reversión** del ejercicio | `activo = t` | `activo = t` |
| 9f | Ejercicios inactivos como al inicio | 2 | 2 |
| 10a | Regresión: `POST /rutinas` | `201`, `favorita=false` | `201`, `false` |
| 10b | `GET /rutinas/{id}` | `200`, misma rutina | `200` |
| 10c | `PUT` acepta `favorita` como antes | `200`, nombre cambiado y `favorita=true` | `200`, nombre cambiado y `true` |
| 10d | Esa rutina (marcada por `PUT`) sale en `?favoritas=true` | sí | sí |
| 10e | Cada usuario ve solo sus rutinas, también con `favoritas=true` | ajeno 1; historial 3 y 1 favorita; vacío `[]` | ajeno 1; historial 3 y 1; vacío `[]` |
| 10f | `demo.historial` intenta alternar la rutina de `demo.ajeno` | `404`; la base sigue `t` | `404`; base `t` |
| 11 | **Datos demo como se encontraron** (`favorita` y `actualizado_en`) | ambas rutinas `f` y `NULL` | ambas `f` y `NULL` |
| 11b | Total de rutinas | 2 | 2 |

### Sentencias SQL medidas

Medidas el 2026-10-15 a nivel HTTP (cliente ASGI mínimo, sin dependencias
nuevas), incluyendo la consulta del usuario del token:

| Petición | Sentencias | Detalle |
|---|---|---|
| `PATCH /rutinas/{id}/favorita` | **3** | usuario del token; `UPDATE rutinas SET favorita = NOT favorita, actualizado_en = now() ... RETURNING`; carga de `ejercicios` para serializar la respuesta |
| `GET /rutinas` (3 rutinas) | **5** | usuario; rutinas; una carga de `ejercicios` **por rutina** (ver el N+1 en Limitaciones) |
| `GET /rutinas?favoritas=true` (1 favorita) | **3** | usuario; rutinas; una carga de `ejercicios` |

---

## Limitaciones y hallazgos

### De esta historia

- **Alternar sin cuerpo.** El `PATCH` no recibe el valor deseado: invierte el que
  está guardado. La app **debe leer el estado actual** (`favorita` en el listado o
  en el detalle) antes de pintar el botón, y usar el valor de la **respuesta** del
  `PATCH`, no suponer el resultado. Si la app mostrara un estado desactualizado
  (otro dispositivo cambió la rutina) y reenviara un toque, el resultado sería el
  contrario del que el usuario cree. Un `PUT` con `favorita` explícito sigue
  disponible para fijar el valor.
- **Efecto sobre `actualizado_en`.** `Rutina.actualizado_en` tiene
  `onupdate=func.now()`, así que cada vez que se alterna la favorita **se
  actualiza** (caso 1c: `NULL` → fecha; la sentencia lleva `actualizado_en = now()`).
  Es decir, marcar una rutina como favorita cuenta como una "edición" para ese
  campo. Se dejó así a propósito; si más adelante se quisiera que `actualizado_en`
  refleje solo cambios de contenido, habría que decidirlo con el equipo.
- **`?favoritas` vacío es `422`.** A diferencia de los filtros de `GET /ejercicios`,
  donde vacío equivale a ausente (ver arriba).
- **Sin tests automatizados:** `tests/` sigue vacío; la verificación es la tabla
  de casos, ejecutada a mano.

### Hallazgos sobre el código existente de rutinas

Observaciones **preexistentes**, para el autor del módulo de rutinas. GYM-157 no
las modificó, no las empeora y no depende de ellas (se verificó que el `PATCH`
funciona igual a pesar de ellas).

1. **N+1 en el listado.** `GET /rutinas` carga los `ejercicios` de cada rutina con
   una consulta aparte, así que hace `1 (usuario) + 1 (rutinas) + N (una por rutina)`
   sentencias. Medido: 3 rutinas → **5** sentencias; 1 rutina (`?favoritas=true`
   con una favorita) → **3**. Crece linealmente con el número de rutinas. Una
   carga ansiosa de la relación (`selectinload`) lo reduciría a 3 fijas.
2. **`validar_ejercicios_entrada` rechaza ejercicios inactivos al editar.** Con un
   ejercicio desactivado dentro de una rutina, `PUT /rutinas/{id}` con la lista de
   ejercicios responde `422 "El ejercicio … está inactivo"` (caso **9c**), aunque
   RN-39 dice que un ejercicio desactivado sigue siendo válido en rutinas ya
   creadas. Un `PUT` que **no** reenvía ejercicios (por ejemplo solo `favorita`)
   sí funciona (caso **9d**), porque no pasa por esa validación. La misma
   validación se aplica al **crear** una rutina, donde rechazar inactivos sí tiene
   sentido; el problema es solo al **editar** una rutina que ya los contiene.
3. **`rutina_service.py` importa FastAPI.** Tiene `from fastapi import
   HTTPException, status` y lanza `HTTPException` 422 desde
   `validar_ejercicios_entrada`. La convención del proyecto (README, "Convenciones")
   es que `services/` no dependa de FastAPI y que sea el router quien traduzca las
   excepciones de dominio a HTTP, como hacen `sesion_service.py` y
   `ejercicio_service.py`. La nueva `alternar_favorita` respeta esa convención
   (devuelve `None` y el router arma el `404`).
