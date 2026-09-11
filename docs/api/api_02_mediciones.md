# API · Mediciones

Referencia completa del recurso `/mediciones`: listar, ver, **editar** y
**eliminar**.

Estado:
- **RF-08 (historial y gráficas de evolución)** · GYM-79 (GYM-129 / GYM-130) — `GET` (listado y detalle).
- **RF-11 (editar o eliminar una medición)** · GYM-80 (GYM-131 / GYM-132 / GYM-133) — `PUT`, `DELETE`.

Las gráficas las arma el cliente con estos datos.
Base URL local: `http://localhost:8001` · Prefijo: `/api/v1`

**Todos los endpoints requieren autenticación** (`Authorization: Bearer
<access_token>`) y operan **solo sobre las mediciones del usuario del token**. Se
apoyan en la dependencia `get_current_user` (`app/api/dependencies.py`),
infraestructura compartida introducida con GYM-79.

Patrón de aislamiento (RF-08, RN-08): `id` y `usuario_id` van **juntos en el
`WHERE`** en las cuatro operaciones sobre `/{id}`. Una medición ajena es
indistinguible de una inexistente → **404, nunca 403**, y no se puede leer,
editar ni borrar.

---

## `GET /api/v1/mediciones`

Lista las mediciones del usuario autenticado, en orden cronológico, con filtro
opcional de rango de fechas.

### Request

| | |
|---|---|
| Método | `GET` |
| Ruta | `/api/v1/mediciones` |
| Auth | **Requerida** — `Authorization: Bearer <access_token>` |
| Cuerpo | No lleva |

El `access_token` es el que devuelve `POST /api/v1/auth/login` (o `/registro`).
**No hay parámetro de usuario** en la ruta ni en la query: el historial es
siempre el del token (RF-08).

#### Parámetros de query (todos opcionales)

| Parámetro | Tipo | Descripción |
|---|---|---|
| `desde` | date (`YYYY-MM-DD`) | Fecha mínima **inclusive**. Filtra por la `fecha` de la medición, no por cuándo se registró. |
| `hasta` | date (`YYYY-MM-DD`) | Fecha máxima **inclusive**. |

- Sin filtros → historial completo.
- Rango sin mediciones → `200` con `[]` (no es error).
- `desde` posterior a `hasta` → `422` (ver más abajo).

### Respuestas

#### `200 OK` — lista de mediciones (`list[MedicionResponse]`)

Orden: por `fecha` de la medición **ascendente** (RN-34), con `creado_en` como
desempate estable cuando dos mediciones comparten fecha.

```json
[
  {
    "id": "8f14e45f-cea1-4c0b-9f6a-1d2e3f4a5b6c",
    "fecha": "2025-01-10",
    "peso_kg": 80.0,
    "imc": 27.7,
    "porcentaje_grasa": null,
    "masa_muscular_kg": null,
    "circunf_cintura_cm": null,
    "circunf_cadera_cm": null,
    "circunf_brazo_cm": null,
    "circunf_pierna_cm": null,
    "circunf_pecho_cm": null,
    "creado_en": "2025-01-12T09:30:00Z"
  }
]
```

| Campo | Descripción |
|---|---|
| `id` | UUID de la medición. |
| `fecha` | Fecha a la que corresponde la medición (la que el usuario declara). |
| `peso_kg` | Peso en kg. Número JSON, no string. |
| `imc` | **Calculado** (RN-12): `peso_kg / (altura_m)²` redondeado a 1 decimal, usando la **altura vigente del usuario** (`usuarios.altura_cm`), no la de la fecha de la medición (RN-30). `null` si el usuario no tiene altura registrada (RN-09). |
| `porcentaje_grasa`, `masa_muscular_kg`, `circunf_*_cm` | Campos opcionales de la medición; `null` si no se registraron. |
| `creado_en` | Marca de tiempo (UTC) de cuando se registró la fila. Puede ser muy posterior a `fecha` (RN-34). |

No se devuelve `usuario_id`: es siempre el del token.

#### `401 Unauthorized` — sin token válido

```json
{ "detail": "No autenticado." }
```

Mismo cuerpo y `WWW-Authenticate: Bearer` en todos los casos: falta el header,
el esquema no es `Bearer`, el token está mal formado, mal firmado o expirado, o
el usuario del token ya no existe. No se distingue cuál (no filtrar información).

#### `422 Unprocessable Entity`

- `desde` / `hasta` con formato que no es una fecha ISO (`YYYY-MM-DD`).
- `desde` posterior a `hasta`:

```json
{ "detail": "`desde` no puede ser posterior a `hasta`." }
```

### Ejemplos `curl`

```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Historial completo
curl http://localhost:8001/api/v1/mediciones \
  -H "Authorization: Bearer $TOKEN"

# Rango de fechas
curl "http://localhost:8001/api/v1/mediciones?desde=2025-02-01&hasta=2025-07-01" \
  -H "Authorization: Bearer $TOKEN"

# Sin token -> 401
curl -i http://localhost:8001/api/v1/mediciones
```

---

## `GET /api/v1/mediciones/{medicion_id}`

Devuelve una sola medición, **siempre que sea del usuario del token**.

### Request

| | |
|---|---|
| Método | `GET` |
| Ruta | `/api/v1/mediciones/{medicion_id}` |
| Auth | **Requerida** — `Authorization: Bearer <access_token>` |
| `medicion_id` | UUID de la medición (en la ruta). |

### Respuestas

| Código | Cuándo | Cuerpo |
|---|---|---|
| `200 OK` | La medición existe y es del usuario autenticado. | `MedicionResponse` (mismo objeto que en el listado). |
| `401 Unauthorized` | Sin token válido. | `{ "detail": "No autenticado." }` |
| `404 Not Found` | El id **no existe** o existe pero es de **otro usuario**. Mismo cuerpo en ambos casos. | `{ "detail": "Medición no encontrada." }` |
| `422 Unprocessable Entity` | `medicion_id` no es un UUID. | error de validación de FastAPI |

**404, no 403** (convención "no filtrar información"): la respuesta no permite
distinguir "no existe" de "es de otra persona". El `id` y el `usuario_id` van
juntos en el `WHERE`, así que una medición ajena simplemente no aparece.

```bash
# Propia -> 200
curl http://localhost:8001/api/v1/mediciones/8f14e45f-cea1-4c0b-9f6a-1d2e3f4a5b6c \
  -H "Authorization: Bearer $TOKEN"

# Id ajeno o inexistente -> 404 (idéntico)
curl -i http://localhost:8001/api/v1/mediciones/00000000-0000-0000-0000-000000000000 \
  -H "Authorization: Bearer $TOKEN"
```

---

## `PUT /api/v1/mediciones/{medicion_id}`

Edita una medición **del usuario del token**. Actualización **parcial**: se
cambian solo los campos presentes en el cuerpo; los omitidos quedan como estaban.

### Request

| | |
|---|---|
| Método | `PUT` |
| Ruta | `/api/v1/mediciones/{medicion_id}` |
| Auth | **Requerida** |
| `Content-Type` | `application/json` |

#### Cuerpo (`MedicionActualizar`) — todos los campos opcionales

| Campo | Tipo | Regla |
|---|---|---|
| `fecha` | date (`YYYY-MM-DD`) | — |
| `peso_kg` | number | **> 0** (RN-03) |
| `porcentaje_grasa` | number | **0 – 99.99** — RN-04 es 0–100 inclusive; el `100` está acotado temporalmente por la columna (ver *Limitaciones*). |
| `masa_muscular_kg` | number | **> 0** (RN-05) |
| `circunf_cintura_cm`, `circunf_cadera_cm`, `circunf_brazo_cm`, `circunf_pierna_cm`, `circunf_pecho_cm` | number | **> 0** (RN-06) |

- **No acepta `usuario_id`** (RN-37): el esquema no lo declara; si llega en el
  cuerpo se **ignora en silencio**, no reasigna la medición.
- Tope superior técnico de los numéricos: `999.99` (`NUMERIC(5,2)`), no es una
  regla de negocio.
- Cuerpo `{}` → no-op, `200` con la medición sin cambios.

### Respuestas

| Código | Cuándo | Cuerpo |
|---|---|---|
| `200 OK` | Editada. | `MedicionResponse` con los valores nuevos y el `imc` recalculado. |
| `401 Unauthorized` | Sin token válido. | `{ "detail": "No autenticado." }` |
| `404 Not Found` | El id no existe **o** es de otro usuario (RN-08). | `{ "detail": "Medición no encontrada." }` |
| `422 Unprocessable Entity` | Algún valor fuera de rango (RN-03 a RN-06), o `medicion_id` no es un UUID. | error de validación de FastAPI |

```bash
# Editar solo el peso (los demás campos no se tocan)
curl -X PUT http://localhost:8001/api/v1/mediciones/8f14e45f-cea1-4c0b-9f6a-1d2e3f4a5b6c \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"peso_kg": 82.5}'

# usuario_id en el cuerpo -> se ignora, la medición sigue siendo del mismo dueño
curl -X PUT http://localhost:8001/api/v1/mediciones/8f14e45f-cea1-4c0b-9f6a-1d2e3f4a5b6c \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"peso_kg": 83, "usuario_id": "00000000-0000-0000-0000-000000000000"}'

# peso_kg <= 0 -> 422
curl -X PUT http://localhost:8001/api/v1/mediciones/8f14e45f-cea1-4c0b-9f6a-1d2e3f4a5b6c \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"peso_kg": 0}'
```

---

## `DELETE /api/v1/mediciones/{medicion_id}`

Elimina **definitivamente** una medición **del usuario del token** (RN-36: no
hay papelera ni baja lógica en este alcance).

### Request

| | |
|---|---|
| Método | `DELETE` |
| Ruta | `/api/v1/mediciones/{medicion_id}` |
| Auth | **Requerida** |
| Cuerpo | No lleva |

### Respuestas

| Código | Cuándo | Cuerpo |
|---|---|---|
| `204 No Content` | Eliminada. | *(vacío)* |
| `401 Unauthorized` | Sin token válido. | `{ "detail": "No autenticado." }` |
| `404 Not Found` | El id no existe **o** es de otro usuario (RN-08). También al borrar por segunda vez la misma medición. | `{ "detail": "Medición no encontrada." }` |
| `422 Unprocessable Entity` | `medicion_id` no es un UUID. | error de validación de FastAPI |

Tras un `204`, la medición desaparece del listado y de `GET /{id}` de inmediato
(borrado físico).

```bash
# Borrar una medición propia -> 204
curl -i -X DELETE http://localhost:8001/api/v1/mediciones/8f14e45f-cea1-4c0b-9f6a-1d2e3f4a5b6c \
  -H "Authorization: Bearer $TOKEN"

# Repetir -> 404
curl -i -X DELETE http://localhost:8001/api/v1/mediciones/8f14e45f-cea1-4c0b-9f6a-1d2e3f4a5b6c \
  -H "Authorization: Bearer $TOKEN"
```

---

## Reglas de negocio aplicadas

| Regla | Exige | Dónde |
|---|---|---|
| RF-08 | El usuario solo ve su propio historial | `listar_mediciones` y `obtener_medicion` filtran `Medicion.usuario_id == usuario.id` en el `WHERE`; el `usuario` sale de `get_current_user` (token), nunca de la URL/body. Ningún endpoint recibe un `usuario_id`. |
| RN-08 | Una medición registrada no puede ser leída, editada ni borrada por otro deportista | Las cuatro funciones (`obtener` / `actualizar` / `eliminar_medicion`) llevan `id` **y** `usuario_id` en el mismo `WHERE`. No hay "buscar por id y luego comparar `usuario_id` en un `if`". Ajena → `None`/`rowcount 0` → 404. |
| RN-36 | Eliminar una medición es definitivo (sin papelera) | `eliminar_medicion` hace `DELETE` físico (`sqlalchemy.delete`), no marca una columna de baja. No hay tabla de papelera. |
| RN-37 | Editar nunca reasigna la medición a otro `usuario_id` | `MedicionActualizar` no declara `usuario_id`; `actualizar_medicion` además hace `cambios.pop("usuario_id", None)` antes de aplicar. El `WHERE` de la búsqueda tampoco permite tocar una fila ajena. |
| RN-03 | `peso_kg` > 0 | `Field(gt=0)` en `MedicionActualizar.peso_kg` → 422 si ≤ 0. |
| RN-04 | `porcentaje_grasa` entre 0 y 100 (inclusive) | `Field(ge=0, le=99.99)` → 422 fuera de rango. El tope está en `99.99` y no en `100` como tapón temporal por la capacidad de la columna (ver *Limitaciones*); RN-04 literal queda pendiente de una migración. |
| RN-05 | `masa_muscular_kg` > 0 | `Field(gt=0)` → 422 si ≤ 0. |
| RN-06 | Circunferencias > 0 | `Field(gt=0)` en los cinco `circunf_*_cm` → 422 si ≤ 0. |
| RN-12 | `IMC = peso_kg / (altura_m)²` | `medicion_service.calcular_imc`, redondeado a 1 decimal (`ROUND_HALF_UP`). Se recalcula en la respuesta del `PUT`. |
| RN-30 | El IMC usa la altura **vigente** del usuario, no la de la fecha de la medición | `calcular_imc` recibe `usuario.altura_cm` (columna `usuarios.altura_cm`), no un valor histórico. |
| RN-34 | Orden por fecha de la medición, no por fecha de registro | `order_by(Medicion.fecha.asc(), Medicion.creado_en.asc())` — `creado_en` solo como desempate. |
| RN-09 | Sin altura registrada no hay IMC | `calcular_imc` devuelve `None` si `altura_cm` es `NULL` o no positiva; el campo sale como `imc: null`. |
| Convención "no filtrar información" | Token inválido / recurso ajeno → respuesta genérica, sin confirmar existencia | `get_current_user` lanza siempre el mismo 401 `"No autenticado."`; `GET` / `PUT` / `DELETE /mediciones/{id}` con un id ajeno o inexistente responden el mismo **404** (nunca 403). |

### IMC — supuestos pendientes de contraste con el documento de reglas

El documento `GymBros_Reglas_de_Negocio_v1` (RN-09 a RN-13) no está en el repo.
Lo implementado se ajusta a RN-12 y RN-30 (que sí se confirmaron). Queda por
confirmar contra el texto oficial:

- **RN-09/10/11**: se asume "sin altura → `imc: null`" y redondeo a 1 decimal.
- **RN-13 (clasificación OMS**: bajo peso / normal / sobrepeso / obesidad**)**:
  **no** se incluye en la respuesta. Si RF-08 la necesita, se añade como campo
  `categoria_imc` calculado junto a `imc`.

---

## Arquitectura (qué hace cada archivo)

| Archivo | Responsabilidad |
|---|---|
| `app/core/security.py` | `decodificar_access_token(token)`: inversa de `crear_access_token`; verifica firma (HS256) y `exp`, exige `sub`. Devuelve el `UUID` del usuario o `None` — no lanza. |
| `app/api/dependencies.py` | `get_current_user`: dependencia de FastAPI con `HTTPBearer`; resuelve el `Usuario` del token o lanza 401. `get_db` sin cambios. |
| `app/schemas/medicion.py` | `MedicionResponse` (salida, numéricos como `float`) y `MedicionActualizar` (entrada del `PUT`: campos editables opcionales con rangos RN-03 a RN-06, `extra="ignore"`, **sin `usuario_id`**). |
| `app/services/medicion_service.py` | `calcular_imc` (RN-12/RN-30/RN-09), `listar_mediciones` (RN-34), `obtener_medicion`, `actualizar_medicion` (parcial, RN-37, RN-08) y `eliminar_medicion` (`DELETE` físico, RN-36, RN-08). Filtro de dueño en el `WHERE` en las cuatro. Sin nada de FastAPI. |
| `app/api/v1/mediciones.py` | Router `/mediciones`: `GET ""`, `GET /{id}`, `PUT /{id}` (404 ajena, 422 rango) y `DELETE /{id}` (`204`, 404 ajena / segundo borrado). Los cuatro con `Depends(get_current_user)`. |
| `app/api/v1/router.py` | Monta `mediciones.router` bajo `/api/v1`. |

Los endpoints se declaran con `def` (no `async def`): acceso a datos síncrono;
FastAPI los corre en un threadpool.

---

## Casos de prueba

Mientras no exista la colección Postman base del proyecto (GYM-94/95/96), los
casos quedan documentados aquí. Requisito previo: base migrada
(`alembic upgrade head`).

### GYM-130 — listado, detalle y aislamiento (`GET`)

Escenario: usuario **A** (con `altura_cm = 170`) con 3 mediciones —
`2025-01-05` (82 kg, *registrada tarde*: su `creado_en` es 60 días anterior al
de las otras), `2025-02-20` (78 kg), `2025-05-01` (74 kg)— y usuario **B**
(**sin** `altura_cm`) con 2 mediciones — `2025-03-10`, `2025-04-10`.

| # | Petición | Resultado esperado |
|---|---|---|
| 1 | `GET /mediciones` con token de A | `200`; **solo las 3 de A**, ninguna de B. |
| 2 | `GET /mediciones` con token de B | `200`; **solo las 2 de B**, ninguna de A. |
| 3 | (orden) mirar el caso 1 | fechas en orden `2025-01-05, 2025-02-20, 2025-05-01` — la registrada tarde cae por su `fecha`, no por `creado_en` (RN-34). |
| 4 | (IMC) mirar el caso 1 | `imc`: 82 kg → `28.4`, 78 → `27.0`, 74 → `25.6` (altura vigente 1.70 m, RN-12/RN-30). |
| 5 | (IMC sin altura) mirar el caso 2 | `imc: null` en las 2 mediciones de B (RN-09). |
| 6 | `GET /mediciones?desde=2025-02-01&hasta=2025-04-30` con token de A | `200`; solo `2025-02-20` (rango inclusivo, por `fecha`). |
| 7 | `GET /mediciones?desde=2025-06-01&hasta=2025-01-01` | `422` (`desde` posterior a `hasta`). |
| 8 | `GET /mediciones/{id_propio}` con el token del dueño | `200`; la medición. |
| 9 | `GET /mediciones/{id_de_B}` con token de **A** | `404` `{"detail": "Medición no encontrada."}` — **no 403**. |
| 10 | `GET /mediciones/{id_de_A}` con token de **B** | `404`, cuerpo idéntico al del caso 9. |
| 11 | `GET /mediciones/00000000-0000-0000-0000-000000000000` con token de A | `404`, cuerpo **idéntico** al caso 9: no se distingue "no existe" de "es de otro". |
| 12 | `GET /mediciones/no-es-uuid` | `422` (validación de UUID de FastAPI). |
| 13 | `GET /mediciones` y `GET /mediciones/{id}` **sin** `Authorization` | `401` `{"detail": "No autenticado."}` en ambas. |

> **Probado en runtime — 2026-09-10.** Los 13 casos se ejecutaron contra el
> stack de `docker compose` (API en `localhost:8001`, PostgreSQL 16, migraciones
> en `444873b25785`) creando los usuarios A y B de verdad vía `POST
> /auth/registro` y sus mediciones en la BD. **Todos pasan.** En particular: el
> token de A nunca devuelve datos de B (ni en el listado ni adivinando el id de
> una medición de B → 404, no 403), y viceversa. Datos de prueba borrados al
> terminar.

### GYM-133 — autorización, edición y borrado (`PUT` / `DELETE`)

Escenario: usuario **A** (`altura_cm = 175`) con 1 medición
(`2025-04-01`, 80 kg, `porcentaje_grasa = 20`, `circunf_cintura_cm = 85`) y
usuario **B** con 1 medición (`2025-04-02`, 65 kg).

| # | Petición | Resultado esperado |
|---|---|---|
| 1 | `PUT /mediciones/{med_A}` con token de A, `{"peso_kg": 82.5}` | `200`; `peso_kg = 82.5`, `imc` recalculado (`26.9` con 1.75 m), **`porcentaje_grasa` y `circunf_cintura_cm` intactos** (actualización parcial). |
| 2 | `PUT /mediciones/{med_B}` con token de **A** | `404` `{"detail": "Medición no encontrada."}` — no 403 (RN-08). |
| 3 | `PUT /mediciones/{med_A}` con token de A, `{"peso_kg": 83, "usuario_id": "<id de B>"}` | `200`; `peso_kg = 83`. El `usuario_id` de la fila **sigue siendo A** (RN-37): el campo se ignoró. |
| 4 | `PUT /mediciones/{med_A}` con `peso_kg = 0` / `-5` / `porcentaje_grasa = 150` / `-1` / `masa_muscular_kg = 0` / `circunf_brazo_cm = 0` | `422` en los seis (RN-03 a RN-06). |
| 5 | `PUT /mediciones/no-es-uuid` → `422` · `PUT /mediciones/{med_A}` sin token → `401` | según lo indicado. |
| 6 | `PUT /mediciones/000…000` con token de A | `404`, cuerpo idéntico al caso 2. |
| 7 | `DELETE /mediciones/{med_A}` con token de **B** | `404`; la medición de A **sigue en la BD** (RN-08). |
| 8 | `DELETE /mediciones/{med_A}` con token de A | `204` sin cuerpo; la medición **desaparece del listado y de la BD** (RN-36). |
| 9 | `DELETE /mediciones/{med_A}` con token de A **otra vez** | `404` (ya no existe). |
| 10 | `DELETE /mediciones/{med_B}` sin token → `401` · `DELETE /mediciones/no-es-uuid` → `422` | según lo indicado. |

> **Probado en runtime — 2026-09-10.** Los 10 casos (más las 6 variantes de
> rango del caso 4) se ejecutaron contra el stack de `docker compose` con dos
> usuarios reales creados vía `POST /auth/registro`. **Todos pasan.** Verificado
> además en la BD: tras el caso 3 la fila conserva su `usuario_id` original; tras
> el caso 8 la fila ya no existe (`SELECT count(*) = 0`). Datos de prueba
> borrados al terminar.

---

## Limitaciones conocidas / en el radar

1. **Sin alta por API.** Hay listado, detalle, edición y borrado; el `POST` para
   crear una medición es otra historia (fuera de RF-08/RF-11).
2. **`PUT` es parcial, no reemplazo.** Aunque el verbo sea `PUT`, se comporta
   como `PATCH`: los campos omitidos no se tocan. No hay forma de "vaciar" a
   `null` un campo opcional en esta versión (un `null` explícito sobre `peso_kg`
   o `fecha` se ignora por ser columnas `NOT NULL`).
3. **Sin paginación.** El historial completo se devuelve de una vez. Con años de
   datos habrá que paginar o limitar por rango.
4. **IMC recalculado con la altura actual (RN-30).** Si el usuario corrige su
   altura, todo el histórico de `imc` cambia en la siguiente consulta. Es lo que
   pide la regla; el cliente no debe cachear `imc` como si fuera inmutable.
5. **`imc` depende de un dato de perfil.** Si `usuarios.altura_cm` es `null`
   (perfil incompleto), todas las mediciones salen con `imc: null` aunque tengan
   peso.
6. **`porcentaje_grasa` — RN-04 vs. columna (tapón temporal).** RN-04 define el
   rango como `0` a `100` **inclusive**, pero la columna es `NUMERIC(4,2)`
   (máx. `99.99`). El schema acota `porcentaje_grasa` a `le=99.99` **como medida
   provisional**, solo para que ningún valor aceptado por la validación pueda
   fallar al persistir (un 500 en el valor límite `100`). **No es la solución
   final:** para cumplir RN-04 al pie de la letra hace falta una **migración que
   ensanche la columna a `NUMERIC(5,2)`** y luego subir el tope del schema a
   `100`. Esa migración **está pendiente de coordinar con el equipo** (no se
   genera desde esta historia para no ramificar heads de Alembic).
7. **Sin tests automatizados** (pytest no se ha visto en el curso); la
   verificación son las tablas de casos de prueba de arriba, ejecutadas a mano.
