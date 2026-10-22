# API · Autenticación

Estado: **RF-01 (registro)** · **RF-02 (login / logout / refresh)** implementados ·
GYM-72, GYM-73. Recuperación de contraseña: pendiente.
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

## `POST /api/v1/auth/login`

Verifica credenciales y devuelve un par de tokens **nuevo** (no reutiliza el del
registro).

### Request — `LoginRequest`

| Campo | Reglas |
|---|---|
| `correo` | Email válido. Se normaliza a minúsculas para buscar (RN-20: `Juan@x` y `juan@x` son la misma cuenta). |
| `password` | Solo se exige que venga (`min_length=1`). **No** se valida la fuerza: si se endurecen las reglas, los usuarios antiguos deben poder entrar. |

### Respuestas

- **`200 OK`** → `TokenResponse` (mismo formato que el registro). Si el hash de la
  contraseña estaba con parámetros de Argon2 más débiles, se regenera en este
  login y el usuario migra sin enterarse (`necesita_rehash`).
- **`401 Unauthorized`** → `{ "detail": "Correo o contraseña incorrectos." }`
  **idéntico** tanto si el correo no existe como si la contraseña es incorrecta
  (RN-24). Cuando el correo no existe se verifica igualmente contra un hash
  ficticio para que la respuesta tarde lo mismo (~170 ms, dominado por Argon2) y
  no se pueda deducir por cronometría qué correos están registrados.

```bash
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"correo":"juan@gmail.com","password":"Secreta123"}'
```

---

## `POST /api/v1/auth/logout`

Revoca un refresh token.

### Request — `RefreshTokenRequest`

| Campo | |
|---|---|
| `refresh_token` | El valor en claro que recibió el cliente. |

### Respuestas

- **`200 OK`** → `{ "mensaje": "Sesión cerrada." }` **siempre**, exista el token,
  no exista, o ya estuviera revocado (RN-26: un logout no revela si el token era
  válido).

Tras el logout, ese refresh ya no sirve para `/refresh` → 401.

---

## `POST /api/v1/auth/refresh`

Canjea un refresh válido por un par de tokens nuevo y **revoca el anterior**
(rotación).

### Request — `RefreshTokenRequest`

Igual que logout: `{ "refresh_token": "..." }`.

### Respuestas

- **`200 OK`** → `TokenResponse` con `access_token` y `refresh_token` nuevos. El
  refresh entregado queda revocado en el acto.
- **`401 Unauthorized`** → `{ "detail": "Refresh token inválido o expirado." }`
  si el token no existe, ya estaba revocado (incluido "ya se rotó una vez"), o
  pasó de `expira_en`. También 401 si la cuenta asociada ya no existe.

**Por qué rotación:** si un token robado se usa después de que el usuario
legítimo ya lo canjeó, el del atacante llega revocado → 401.

---

## Reglas de negocio aplicadas

| Regla | Exige | Dónde |
|---|---|---|
| RN-20 | Correo único global | `UNIQUE` en `usuarios.correo` + captura de `IntegrityError` en `auth_service.registrar_usuario` |
| RN-21 | Contraseña ≥ 8, al menos una letra y un número | Validador de `password` en `schemas/auth.py` (`Field(min_length=8, max_length=128)` + regex) |
| RN-22 | Hash Argon2id, nunca en claro ni en logs | `core/security.hashear_password` (Argon2id por defecto de `argon2-cffi`) + handler de 422 en `main.py` |
| RN-23 | El registro exitoso deja sesión iniciada | `registrar_usuario` emite y devuelve `access` + `refresh` |
| RN-24 | Login fallido: mensaje genérico, sin revelar si el correo existe | `autenticar_usuario` — mismo `CredencialesInvalidasError` en ambos casos + verificación contra `HASH_FICTICIO` cuando no hay usuario (iguala el tiempo) |
| RN-25 | Access corto + refresh largo | `ACCESS_TOKEN_MINUTOS=15` en el JWT, `REFRESH_TOKEN_DIAS=30` en `refresh_tokens.expira_en` |
| RN-26 | Logout revoca el refresh token | `cerrar_sesion` marca `revocado=True`; responde 200 igual si no existe o ya estaba revocado |
| Ley 1581 | Capturar el consentimiento de tratamiento de datos | Campo obligatorio `consentimiento_datos` + columnas `consentimiento_datos` / `consentimiento_en` (migración `444873b25785`) |

---

## Arquitectura (qué hace cada archivo)

| Archivo | Responsabilidad |
|---|---|
| `app/api/dependencies.py` | `get_db`: cede una `Session` y la cierra en `finally` (la conexión vuelve al pool aunque el endpoint lance). |
| `app/core/security.py` | `hashear_password` / `verificar_password` / `necesita_rehash` (Argon2id), `hashear_token` (SHA-256 de un opaco, para guardar y para buscar), `HASH_FICTICIO` (dummy para el timing del login), `crear_access_token` (JWT HS256), `generar_refresh_token` (opaco + hash). Sin acceso a BD. |
| `app/schemas/auth.py` | `RegistroRequest`, `LoginRequest`, `RefreshTokenRequest` (logout + refresh), `TokenResponse`, `MensajeResponse`. |
| `app/services/auth_service.py` | `emitir_par_de_tokens` (helper, no hace `commit`), `registrar_usuario`, `autenticar_usuario` (RN-24), `cerrar_sesion` (RN-26), `rotar_refresh_token` (rotación). Errores: `CorreoYaRegistradoError` → 409, `CredencialesInvalidasError` → 401, `RefreshInvalidoError` → 401. |
| `app/api/v1/auth.py` | Router `/auth`: `POST /registro` (201), `/login`, `/logout`, `/refresh`. Traduce los errores de servicio a `HTTPException`. |
| `app/api/v1/router.py` | `api_router` con prefijo `/api/v1`; monta `auth.router`. |
| `app/main.py` | Monta `api_router` y registra el handler de `RequestValidationError` (RN-22). |

Los endpoints se declaran con `def` (no `async def`): el acceso a datos es
síncrono (SQLAlchemy sin driver async); FastAPI ejecuta las funciones `def` en
un threadpool.

### Configuración relevante (`app/core/config.py`, `.env`)

`ACCESS_TOKEN_MINUTOS=15` · `REFRESH_TOKEN_DIAS=30` · `RECUPERACION_TOKEN_MINUTOS=60`
(aún sin usar, RN-27) · `JWT_ALGORITHM=HS256` · `JWT_SECRET` (rechazado si es el
valor de ejemplo o mide < 32 caracteres) · `DATABASE_URL`.

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
3. **Sin rate limiting ni captcha** en login ni registro. Es lo que hace viable
   la fuerza bruta de contraseñas contra un correo conocido.
4. **Timing del login: "suficientemente bueno", no constante.** El hash ficticio
   iguala el coste de Argon2 (lo que domina, ~170 ms), pero la ruta "usuario
   existe" hace además el `INSERT` del refresh + `commit`. La diferencia medida
   es de pocos ms, dentro del ruido.
5. **Sin tests automatizados**; la verificación fue smoke manual end-to-end
   (registro 201/409/422; login 200/401 con tiempos comparables; logout 200
   siempre; refresh rota y revoca; reusar un refresh rotado → 401).

---

## Pendiente (siguiente slice de RF-02)

- `POST /auth/recuperar-password` y `POST /auth/reset-password` (RN-27: enlace
  que expira en 1 h, un solo uso). Modelo `TokenRecuperacion` ya existe.
- Al cambiar la contraseña (reset), **revocar todos los refresh del usuario** en
  cascada: si no, quien robó la cuenta sigue dentro tras la recuperación.
- `core/mailer.py` + variables SMTP para enviar el enlace. Por ahora el token
  iría al log.
- Detección de reúso de refresh que "mata toda la familia" de tokens (hoy la
  rotación solo revoca el token concreto).
