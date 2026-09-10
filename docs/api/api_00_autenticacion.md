# API · Autenticación

Estado: **RF-01 (registro) implementado** · GYM-72
Base URL local: `http://localhost:8001` · Prefijo: `/api/v1`

---

## `POST /api/v1/auth/registro`

Crea una cuenta y **deja la sesión iniciada**: la respuesta trae el par de
tokens, no un simple "usuario creado" (RN-23).

### Request

| | |
|---|---|
| Método | `POST` |
| Ruta | `/api/v1/auth/registro` |
| `Content-Type` | `application/json` |
| Auth | No requiere |

#### Cuerpo (`RegistroRequest`)

| Campo | Tipo | Reglas |
|---|---|---|
| `correo` | string | Formato de email válido (`EmailStr`). Se normaliza a minúsculas antes de guardar. **No se comprueba que el dominio ni el buzón existan** (ver *Limitaciones*). |
| `password` | string | 8–128 caracteres, **al menos una letra y un número** (RN-21). |
| `nombre` | string | 1–100 caracteres; se recortan los espacios de los extremos, no puede quedar vacío. |
| `consentimiento_datos` | boolean | Debe ser `true`. Obligatorio para registrarse (Ley 1581). |

No se envía `usuario_id` ni ningún campo de perfil opcional (sexo, altura, foto…);
eso es materia de otro endpoint.

```json
{
  "correo": "juan@gmail.com",
  "password": "Secreta123",
  "nombre": "Juan",
  "consentimiento_datos": true
}
```

### Respuestas

#### `201 Created` — cuenta creada (`TokenResponse`)

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "9rdJSPc1ow4I7D1_xcSqXqZS_UfczM4qxODq8GeJt_A",
  "token_type": "bearer",
  "expires_in": 900
}
```

| Campo | Descripción |
|---|---|
| `access_token` | JWT firmado (HS256). Claims: `sub` = `usuario.id` (string), `iat`, `exp`. |
| `refresh_token` | Valor opaco (`secrets.token_urlsafe(32)`). En la base solo se guarda su hash SHA-256, nunca el valor en claro. |
| `token_type` | Siempre `"bearer"`. |
| `expires_in` | Segundos de vida del `access_token` (`ACCESS_TOKEN_MINUTOS` × 60 = 900 con la config actual). |

Efecto en base de datos:

- Fila en `usuarios` con `hash_password` Argon2id, `consentimiento_datos = true` y
  `consentimiento_en` con la marca de tiempo del registro.
- Fila en `refresh_tokens` con `token_hash` (SHA-256), `revocado = false` y
  `expira_en = ahora + REFRESH_TOKEN_DIAS` (30 días).

#### `409 Conflict` — correo ya registrado (RN-20)

```json
{ "detail": "El correo ya está registrado." }
```

La unicidad la garantiza la restricción `UNIQUE` sobre `usuarios.correo`. El
servicio intenta el `INSERT` y captura el `IntegrityError`; **no** hace un
`SELECT` previo (dos peticiones simultáneas con el mismo correo lo pasarían las
dos). Ante el conflicto se hace `rollback` y no queda ninguna fila a medias.

#### `422 Unprocessable Entity` — cuerpo inválido

Formato de `correo` inválido, `password` que incumple RN-21, `nombre` vacío o
`consentimiento_datos` distinto de `true`.

```json
{
  "detail": [
    { "type": "value_error", "loc": ["body", "password"],
      "msg": "Value error, La contraseña debe incluir al menos una letra y un número." }
  ]
}
```

> **RN-22 — la contraseña no se filtra.** La respuesta 422 por defecto de FastAPI
> incluye `input` con el valor que falló. Un `exception_handler` de
> `RequestValidationError` (en `app/main.py`) elimina `input` de todos los
> errores y, además, elimina `ctx` cuando el error apunta a un campo marcado
> como sensible (`_CAMPOS_SENSIBLES = {"password"}`), porque algunos validadores
> guardan el valor dentro de `ctx`. Verificado: con `password = "abc"` o
> `"abcdefgh"` el valor no aparece en ningún punto de la respuesta.

### Ejemplos `curl`

```bash
# Registro correcto
curl -X POST http://localhost:8001/api/v1/auth/registro \
  -H 'Content-Type: application/json' \
  -d '{"correo":"juan@gmail.com","password":"Secreta123","nombre":"Juan","consentimiento_datos":true}'

# Correo repetido -> 409
curl -X POST http://localhost:8001/api/v1/auth/registro \
  -H 'Content-Type: application/json' \
  -d '{"correo":"juan@gmail.com","password":"Otra12345","nombre":"Juan","consentimiento_datos":true}'

# password sin número -> 422
curl -X POST http://localhost:8001/api/v1/auth/registro \
  -H 'Content-Type: application/json' \
  -d '{"correo":"otro@gmail.com","password":"abcdefgh","nombre":"Otro","consentimiento_datos":true}'
```

---

## Reglas de negocio aplicadas

| Regla | Exige | Dónde |
|---|---|---|
| RN-20 | Correo único global | `UNIQUE` en `usuarios.correo` + captura de `IntegrityError` en `auth_service.registrar_usuario` |
| RN-21 | Contraseña ≥ 8, al menos una letra y un número | Validador de `password` en `schemas/auth.py` (`Field(min_length=8, max_length=128)` + regex) |
| RN-22 | Hash Argon2id, nunca en claro ni en logs | `core/security.hashear_password` (Argon2id por defecto de `argon2-cffi`) + handler de 422 en `main.py` |
| RN-23 | El registro exitoso deja sesión iniciada | `registrar_usuario` emite y devuelve `access` + `refresh` |
| Ley 1581 | Capturar el consentimiento de tratamiento de datos | Campo obligatorio `consentimiento_datos` + columnas `consentimiento_datos` / `consentimiento_en` (migración `444873b25785`) |

---

## Arquitectura (qué hace cada archivo)

| Archivo | Responsabilidad |
|---|---|
| `app/api/dependencies.py` | `get_db`: cede una `Session` y la cierra en `finally` (la conexión vuelve al pool aunque el endpoint lance). |
| `app/core/security.py` | `hashear_password` / `verificar_password` (Argon2id), `necesita_rehash` (`check_needs_rehash`), `crear_access_token` (JWT HS256), `generar_refresh_token` (opaco + hash SHA-256). |
| `app/schemas/auth.py` | `RegistroRequest` (validaciones RN-21 y Ley 1581), `TokenResponse`. |
| `app/services/auth_service.py` | `registrar_usuario`: normaliza correo, hashea, crea usuario, guarda el hash del refresh, hace `commit` y devuelve los tokens. `CorreoYaRegistradoError` → 409. |
| `app/api/v1/auth.py` | Router `/auth`; `POST /registro` → 201, traduce `CorreoYaRegistradoError` a `HTTPException(409)`. |
| `app/api/v1/router.py` | `api_router` con prefijo `/api/v1`; monta `auth.router`. |
| `app/main.py` | Monta `api_router` y registra el handler de `RequestValidationError` (RN-22). |

Los endpoints se declaran con `def` (no `async def`): el acceso a datos es
síncrono (SQLAlchemy sin driver async); FastAPI ejecuta las funciones `def` en
un threadpool.

### Configuración relevante (`app/core/config.py`, `.env`)

`ACCESS_TOKEN_MINUTOS=15` · `REFRESH_TOKEN_DIAS=30` · `JWT_ALGORITHM=HS256` ·
`JWT_SECRET` (rechazado si es el valor de ejemplo o mide < 32 caracteres) ·
`DATABASE_URL`.

---

## Limitaciones conocidas / en el radar

1. **`consentimiento_datos` es redundante.** Vale `true` en toda fila que exista
   (sin consentimiento no se crea la cuenta). `consentimiento_en` sola ya dice
   lo mismo y además *cuándo*. Una columna que nunca varía induce a error a
   quien la consulte. No se quita ahora porque cuesta otra migración; pendiente
   de decisión.
2. **El registro no verifica que el correo exista ni reciba mail.** Solo se
   valida el formato. Un dominio inexistente o un typo (`@gmial.com`) pasan; un
   buzón inexistente en un dominio real (`nadie@gmail.com`) es el caso común y no
   hay forma de detectarlo aquí. La verificación real es un enlace de
   confirmación que el usuario abre — materia de **RF-02**. Se probó meter un
   `check_deliverability` por DNS en el validador y se descartó: mete una llamada
   de red y un modo de falla nuevo (DNS caído → todos los registros fallan) en el
   camino crítico, a cambio de atajar solo el caso raro. Avisar de typos de
   dominio se hace mejor en el frontend, sin bloquear.
3. **Sin rate limiting ni captcha** en el registro.
4. **Sin tests automatizados**; la verificación fue smoke manual end-to-end
   (201 / 409 / 422 sin fuga, fila en BD, hash SHA-256 del refresh).

---

## Pendiente para GYM-73 (login)

Las primitivas ya están implementadas y probadas en `app/core/security.py`; el
login solo tiene que conectarlas:

- `verificar_password(hash, password) -> bool` — no lanza.
- `necesita_rehash(hash) -> bool` — envuelve `check_needs_rehash`; `False` ante
  un hash ilegible. Llamarla **tras** un `verificar_password` correcto: si
  devuelve `True`, `usuario.hash_password = hashear_password(password)` y
  `commit`. Así los usuarios antiguos migran solos si se suben los parámetros de
  Argon2. Probado: hash actual → `False`, hash con parámetros débiles → `True`.
- Conviene igualar el tiempo de respuesta cuando el correo no existe (verificar
  contra un hash ficticio) para no filtrar qué correos están registrados.
- Todavía no existe endpoint que canjee el `refresh_token`.
