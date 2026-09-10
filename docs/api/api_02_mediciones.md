# API · Historial de mediciones

Estado: **RF-08 (historial y gráficas de evolución)** — listado implementado ·
GYM-79 (GYM-129 / GYM-130). Gráficas: las arma el cliente con estos datos.
Base URL local: `http://localhost:8001` · Prefijo: `/api/v1`

Este endpoint **requiere autenticación**: devuelve el historial del usuario del
token y de nadie más. Se apoya en la dependencia `get_current_user`
(`app/api/dependencies.py`), infraestructura compartida añadida en esta misma
rama.

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

## Reglas de negocio aplicadas

| Regla | Exige | Dónde |
|---|---|---|
| RF-08 | El usuario solo ve su propio historial | `listar_mediciones` y `obtener_medicion` filtran `Medicion.usuario_id == usuario.id` en el `WHERE`; el `usuario` sale de `get_current_user` (token), nunca de la URL/body. Ningún endpoint recibe un `usuario_id`. |
| RN-12 | `IMC = peso_kg / (altura_m)²` | `medicion_service.calcular_imc`, redondeado a 1 decimal (`ROUND_HALF_UP`). |
| RN-30 | El IMC usa la altura **vigente** del usuario, no la de la fecha de la medición | `calcular_imc` recibe `usuario.altura_cm` (columna `usuarios.altura_cm`), no un valor histórico. |
| RN-34 | Orden por fecha de la medición, no por fecha de registro | `order_by(Medicion.fecha.asc(), Medicion.creado_en.asc())` — `creado_en` solo como desempate. |
| RN-09 | Sin altura registrada no hay IMC | `calcular_imc` devuelve `None` si `altura_cm` es `NULL` o no positiva; el campo sale como `imc: null`. |
| Convención "no filtrar información" | Token inválido / recurso ajeno → respuesta genérica, sin confirmar existencia | `get_current_user` lanza siempre el mismo 401 `"No autenticado."`; `GET /mediciones/{id}` con un id ajeno o inexistente responde el mismo **404** (nunca 403). |

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
| `app/schemas/medicion.py` | `MedicionResponse` (salida). Sin esquema de entrada: este endpoint no crea ni edita. Numéricos como `float` (número JSON). |
| `app/services/medicion_service.py` | `calcular_imc(peso_kg, altura_cm)` (RN-12/RN-30/RN-09), `listar_mediciones(db, *, usuario, desde, hasta)` (RN-34) y `obtener_medicion(db, *, usuario, medicion_id)`. Filtro de dueño en el `WHERE`. Sin nada de FastAPI. |
| `app/api/v1/mediciones.py` | Router `/mediciones`: `GET ""` (listado, valida `desde <= hasta` → 422) y `GET /{medicion_id}` (detalle, 404 si no es del usuario). Ambos con `Depends(get_current_user)`. |
| `app/api/v1/router.py` | Monta `mediciones.router` bajo `/api/v1`. |

Los endpoints se declaran con `def` (no `async def`): acceso a datos síncrono;
FastAPI los corre en un threadpool.

---

## Casos de prueba (GYM-130)

Mientras no exista la colección Postman base del proyecto (GYM-94/95/96), los
casos quedan documentados aquí. Requisito previo: base migrada
(`alembic upgrade head`).

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

---

## Limitaciones conocidas / en el radar

1. **Solo lectura.** Hay listado (`GET ""`) y detalle (`GET /{id}`), pero no
   alta, edición ni borrado de mediciones por API en esta historia.
2. **Sin paginación.** El historial completo se devuelve de una vez. Con años de
   datos habrá que paginar o limitar por rango.
3. **IMC recalculado con la altura actual (RN-30).** Si el usuario corrige su
   altura, todo el histórico de `imc` cambia en la siguiente consulta. Es lo que
   pide la regla; el cliente no debe cachear `imc` como si fuera inmutable.
4. **`imc` depende de un dato de perfil.** Si `usuarios.altura_cm` es `null`
   (perfil incompleto), todas las mediciones salen con `imc: null` aunque tengan
   peso.
5. **Sin tests automatizados** (pytest no se ha visto en el curso); la
   verificación es la tabla de casos de prueba (GYM-130) más abajo.
