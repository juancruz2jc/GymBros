# Reporte de pruebas de la API · rama `dev`

- **Fecha de ejecución:** 2026-09-16 21:02 (hora Colombia)
- **Rama / commit:** `dev` @ `b6774ef` (incluye `fix/porcentaje-grasa-numeric-5-2`, `dev-jazmin` y GYM-81)
- **Entorno:** `docker compose` local (PostgreSQL 16 + API en `http://localhost:8001`), migración `9579bae4a653 (head)`
- **Método:** pruebas de caja negra por HTTP contra la API real, con verificación en base de datos cuando aplica. Se crean usuarios `e2e.*@test.com` y se borran al terminar.
- **Nota de horario:** se ejecutó cuando en Colombia era 2026-09-16 y en UTC ya era 2026-09-17; por eso aparecen las fallas de zona horaria (H-05).

**Leyenda:** ✅ cumple · ❌ falla (bug: error 500, regla de negocio rota o dato corrupto) · ⚠️ observación (no hay regla definida o es un riesgo que el equipo debe decidir)

## Resumen

| Total | ✅ OK | ❌ Fallas | ⚠️ Observaciones |
|---:|---:|---:|---:|
| 400 | 350 | 26 | 24 |

### Por endpoint

| Endpoint | Casos | ✅ | ❌ | ⚠️ | Hallazgos |
|---|---:|---:|---:|---:|---|
| [`GET /salud`](#get-salud) | 4 | 2 | 0 | 2 | O-12 |
| [`POST /auth/registro`](#post-authregistro) | 39 | 37 | 0 | 2 | O-07, O-08 |
| [`POST /auth/login`](#post-authlogin) | 14 | 13 | 0 | 1 | O-02 |
| [`POST /auth/refresh`](#post-authrefresh) | 10 | 9 | 0 | 1 | O-04 |
| [`POST /auth/logout`](#post-authlogout) | 7 | 6 | 0 | 1 | O-03 |
| [`GET /usuarios/me`](#get-usuariosme) | 18 | 18 | 0 | 0 | — |
| [`PUT /usuarios/me`](#put-usuariosme) | 44 | 37 | 3 | 4 | H-06, H-07, O-07, O-08 |
| [`GET /ejercicios`](#get-ejercicios) | 20 | 17 | 0 | 3 | O-01, O-11 |
| [`POST /mediciones`](#post-mediciones) | 74 | 56 | 11 | 7 | H-01, H-05, H-08, H-09, O-05, O-06, O-07, O-09 |
| [`GET /mediciones`](#get-mediciones) | 30 | 30 | 0 | 0 | — |
| [`GET /mediciones/{id}`](#get-medicionesid) | 21 | 21 | 0 | 0 | — |
| [`PUT /mediciones/{id}`](#put-medicionesid) | 41 | 35 | 3 | 3 | H-02, H-08, O-05, O-10 |
| [`DELETE /mediciones/{id}`](#delete-medicionesid) | 24 | 24 | 0 | 0 | — |
| [`GET /mediciones/inactividad`](#get-medicionesinactividad) | 24 | 16 | 8 | 0 | H-03, H-05, H-10 |
| [`GET /mediciones/comparar`](#get-medicionescomparar) | 26 | 25 | 1 | 0 | H-04 |
| [`Cuenta eliminada`](#cuenta-eliminada) | 4 | 4 | 0 | 0 | — |

### Protección con login

Los **9 endpoints privados** (`/usuarios/me` GET y PUT, y los 7 de `/mediciones`) se atacaron con 13 variantes cada uno: sin header, `Bearer` vacío, esquema `Basic`, token sin esquema, token basura, **token expirado**, firmado con **otro secreto**, **`alg=none`**, **payload manipulado** con el `sub` de otro usuario, usuario inexistente, `sub` que no es UUID, **sin `exp`** y el **refresh token usado como access**.

**Resultado: los 117 intentos devolvieron 401.** Ningún endpoint privado se puede usar sin un login válido. La única ruta de negocio sin login es `GET /ejercicios` (ver O-01).

## Hallazgos (bugs) por responsable

| ID | Severidad | Endpoint | Responsable | Resumen | Casos |
|---|---|---|---|---|---:|
| [H-01](#h-01) | 🔴 Alta | `POST /mediciones` | Jazmin Mera | `POST /mediciones` responde 500 con valores de 1000 o más, `1e308` o `Infinity` | 8 |
| [H-02](#h-02) | 🔴 Alta | `PUT /mediciones/{id}` | juancruz2jc | `PUT /mediciones/{id}` permite poner una fecha futura (rompe RN-70) | 2 |
| [H-03](#h-03) | 🔴 Alta | `GET /mediciones/inactividad` | Jazmin Mera (se desencadena por H-02 de juancruz2jc) | `GET /mediciones/inactividad` devuelve días negativos | 1 |
| [H-04](#h-04) | 🔴 Alta | `GET /mediciones/comparar` | Luise Olave | `GET /mediciones/comparar` responde 500 si hay 2 mediciones el mismo día | 1 |
| [H-05](#h-05) | 🟠 Media | `POST /mediciones · GET /mediciones/inactividad` | Jazmin Mera | Zona horaria: el servidor usa UTC; de 7 p. m. a medianoche en Colombia las fechas quedan corridas un día | 7 |
| [H-06](#h-06) | 🔴 Alta | `PUT /usuarios/me` | Luise Olave | `PUT /usuarios/me` con `{"nombre": null}` responde 500 | 1 |
| [H-07](#h-07) | 🟠 Media | `PUT /usuarios/me` | Luise Olave | `PUT /usuarios/me` acepta un nombre de solo espacios y no recorta | 2 |
| [H-08](#h-08) | 🟠 Media | `POST /mediciones · PUT /mediciones/{id}` | Jazmin Mera (POST) · juancruz2jc (PUT) | Un peso de `0.001` se guarda como `0.00` (rompe RN-03 peso > 0) | 2 |
| [H-09](#h-09) | 🟡 Baja | `POST /mediciones` | Jazmin Mera | `POST /mediciones` acepta `peso_kg: true` y lo guarda como 1.0 | 1 |
| [H-10](#h-10) | 🟡 Baja | `GET /mediciones/inactividad` | Jazmin Mera | `GET /mediciones/inactividad` devuelve `ultima_medicion` como datetime (`2026-09-11T00:00:00`) | 1 |

### H-01

**`POST /mediciones` responde 500 con valores de 1000 o más, `1e308` o `Infinity`**

- **Severidad:** 🔴 Alta
- **Endpoint:** `POST /mediciones`
- **Responsable:** Jazmin Mera
- **Dónde:** `gymbros-api/app/schemas/medicion.py:20` (`MedicionCrear`)
- **Causa:** `MedicionCrear` solo valida `gt=0`, sin tope superior. Las columnas son `NUMERIC(5,2)` (máx. 999.99), así que PostgreSQL lanza `numeric field overflow` y la API devuelve 500. `MedicionActualizar` (PUT) sí tiene el tope.
- **Cómo reproducir:** `POST /api/v1/mediciones` con `{"fecha": "2026-09-10", "peso_kg": 1000}` → **500 Internal Server Error**
- **Arreglo sugerido:** Reusar en `MedicionCrear` los tipos `_Peso`, `_Grasa` y `_Positivo` que ya existen para el PUT (`le=999.99`). Rechazar `inf`/`nan` con `allow_inf_nan=False`.
- **Casos que fallan:** `peso 1000 (excede NUMERIC(5,2))`; `peso 1e308`; `masa muscular 1000`; `brazo 1000`; `pierna 1000`; `pecho 1000`; `cintura 1000`; `peso Infinity`

### H-02

**`PUT /mediciones/{id}` permite poner una fecha futura (rompe RN-70)**

- **Severidad:** 🔴 Alta
- **Endpoint:** `PUT /mediciones/{id}`
- **Responsable:** juancruz2jc
- **Dónde:** `gymbros-api/app/schemas/medicion.py:112` (`MedicionActualizar.fecha`)
- **Causa:** RN-70 solo se valida en el servicio de creación. El schema de edición declara `fecha: date | None` sin ninguna validación.
- **Cómo reproducir:** `PUT /api/v1/mediciones/{id}` con `{"fecha": "9999-12-31"}` → **200** y la medición queda con fecha 9999-12-31.
- **Arreglo sugerido:** Agregar un `field_validator` a `fecha` que rechace fechas posteriores a hoy (hora de Colombia, ver H-05). Acordar con el POST si la respuesta es 400 o 422.
- **Casos que fallan:** `fecha futura +3 días (RN-70)`; `fecha 9999-12-31 (RN-70)`

### H-03

**`GET /mediciones/inactividad` devuelve días negativos**

- **Severidad:** 🔴 Alta
- **Endpoint:** `GET /mediciones/inactividad`
- **Responsable:** Jazmin Mera (se desencadena por H-02 de juancruz2jc)
- **Dónde:** `gymbros-api/app/services/medicion_service.py:114` (`obtener_estado_inactividad`)
- **Causa:** Con una medición futura (colada por H-02), `hoy − fecha` da negativo y `esta_inactivo` queda en `false`.
- **Cómo reproducir:** Editar una medición a `9999-12-31` y llamar `GET /api/v1/mediciones/inactividad` → `dias_desde_ultima_medicion: -2912183`.
- **Arreglo sugerido:** Corregir H-02 primero. Además, como defensa, calcular la última medición solo con `fecha <= hoy`.
- **Casos que fallan:** `con una medición futura (colada por PUT) los días no son negativos`

### H-04

**`GET /mediciones/comparar` responde 500 si hay 2 mediciones el mismo día**

- **Severidad:** 🔴 Alta
- **Endpoint:** `GET /mediciones/comparar`
- **Responsable:** Luise Olave
- **Dónde:** `gymbros-api/app/services/medicion_service.py:201` (`comparar_mediciones`)
- **Causa:** Usa `scalar_one_or_none()` por fecha, pero la API permite registrar varias mediciones el mismo día → `MultipleResultsFound`.
- **Cómo reproducir:** Crear 2 mediciones con la misma fecha y llamar `GET /api/v1/mediciones/comparar?fecha1=<esa fecha>&fecha2=<otra>` → **500**.
- **Arreglo sugerido:** Decidir la regla en equipo: (a) tomar la última del día (`order_by(Medicion.creado_en.desc()).limit(1)` + `.scalars().first()`), o (b) prohibir más de una medición por día en el POST/PUT (restricción única `usuario_id, fecha`). Quitar también `func.date(...)` (la columna ya es `Date`) y el import duplicado de `IMCRespuesta`.
- **Casos que fallan:** `fecha con 2 mediciones el mismo día`

### H-05

**Zona horaria: el servidor usa UTC; de 7 p. m. a medianoche en Colombia las fechas quedan corridas un día**

- **Severidad:** 🟠 Media
- **Endpoint:** `POST /mediciones · GET /mediciones/inactividad`
- **Responsable:** Jazmin Mera
- **Dónde:** `gymbros-api/app/services/medicion_service.py:32` (`crear_medicion`) y `:114` (`date.today()`)
- **Causa:** `datetime.now(timezone.utc)` y `date.today()` dentro del contenedor dan la fecha UTC (5 h adelante de Colombia).
- **Cómo reproducir:** A las 9 p. m. de Colombia: `POST` con la fecha de **mañana** → 201. `GET /inactividad` con última medición hace 29 días → `dias: 30, esta_inactivo: true` (la alerta sale un día antes).
- **Arreglo sugerido:** Calcular "hoy" con `datetime.now(ZoneInfo("America/Bogota")).date()` en un solo helper y usarlo en RN-70 (POST y PUT) y en inactividad.
- **Casos que fallan:** `RN-70: mañana en Colombia (2026-09-17) sin zona`; `última hace 5 días → activo`; `última hace 0 días → esta_inactivo=False`; `última hace 29 días → esta_inactivo=False`; `última hace 30 días → esta_inactivo=True`; `última hace 31 días → esta_inactivo=True`; `última hace 400 días → esta_inactivo=True`

### H-06

**`PUT /usuarios/me` con `{"nombre": null}` responde 500**

- **Severidad:** 🔴 Alta
- **Endpoint:** `PUT /usuarios/me`
- **Responsable:** Luise Olave
- **Dónde:** `gymbros-api/app/schemas/usuario.py:18` (`UsuarioUpdate`) y `gymbros-api/app/services/usuario_service.py:13`
- **Causa:** `nombre: Optional[str]` acepta `null`; el servicio hace `setattr` con `exclude_unset` y la columna es `NOT NULL` → `IntegrityError`.
- **Cómo reproducir:** `PUT /api/v1/usuarios/me` con `{"nombre": null}` → **500 Internal Server Error**.
- **Arreglo sugerido:** Rechazar `null` en `nombre` (validator) o ignorar `None` en columnas obligatorias, igual que hace `actualizar_medicion` con `_CAMPOS_OBLIGATORIOS`.
- **Casos que fallan:** `nombre null`

### H-07

**`PUT /usuarios/me` acepta un nombre de solo espacios y no recorta**

- **Severidad:** 🟠 Media
- **Endpoint:** `PUT /usuarios/me`
- **Responsable:** Luise Olave
- **Dónde:** `gymbros-api/app/schemas/usuario.py:18` (`UsuarioUpdate`)
- **Causa:** `min_length=2` cuenta los espacios. El registro (`RegistroRequest`) sí recorta y rechaza vacío; la edición no.
- **Cómo reproducir:** `PUT /api/v1/usuarios/me` con `{"nombre": "     "}` → **200** y el perfil queda sin nombre visible.
- **Arreglo sugerido:** Copiar el `field_validator` `_nombre_no_vacio` de `schemas/auth.py` a `UsuarioUpdate`.
- **Casos que fallan:** `nombre solo espacios`; `nombre con espacios alrededor se recorta`

### H-08

**Un peso de `0.001` se guarda como `0.00` (rompe RN-03 peso > 0)**

- **Severidad:** 🟠 Media
- **Endpoint:** `POST /mediciones · PUT /mediciones/{id}`
- **Responsable:** Jazmin Mera (POST) · juancruz2jc (PUT)
- **Dónde:** `gymbros-api/app/schemas/medicion.py:20` y `:91` (`_Peso`)
- **Causa:** `gt=0` deja pasar 0.001; la columna `NUMERIC(5,2)` lo redondea a 0.00.
- **Cómo reproducir:** `POST /api/v1/mediciones` con `{"fecha": "2026-09-10", "peso_kg": 0.001}` → 201 con `peso_kg: 0.0`.
- **Arreglo sugerido:** Usar `ge=0.01` en peso, masa y circunferencias (o `condecimal(max_digits=5, decimal_places=2, gt=0)`).
- **Casos que fallan:** `peso 0.001 (se guardaría 0.00)`; `peso 0.001 (se guardaría 0.00)`

### H-09

**`POST /mediciones` acepta `peso_kg: true` y lo guarda como 1.0**

- **Severidad:** 🟡 Baja
- **Endpoint:** `POST /mediciones`
- **Responsable:** Jazmin Mera
- **Dónde:** `gymbros-api/app/schemas/medicion.py:20` (`MedicionCrear`)
- **Causa:** Pydantic en modo laxo convierte `true` a `1.0`.
- **Cómo reproducir:** `POST /api/v1/mediciones` con `{"fecha": "2026-09-10", "peso_kg": true}` → 201 con `peso_kg: 1.0`.
- **Arreglo sugerido:** Usar `StrictFloat` o `ConfigDict(strict=True)` en los campos numéricos (resuelve también O-07).
- **Casos que fallan:** `peso booleano true`

### H-10

**`GET /mediciones/inactividad` devuelve `ultima_medicion` como datetime (`2026-09-11T00:00:00`)**

- **Severidad:** 🟡 Baja
- **Endpoint:** `GET /mediciones/inactividad`
- **Responsable:** Jazmin Mera
- **Dónde:** `gymbros-api/app/schemas/medicion.py:64` (`InactividadRespuesta`)
- **Causa:** Declara `ultima_medicion: Optional[datetime]` cuando la columna es `Date`; el resto de la API devuelve `YYYY-MM-DD`.
- **Cómo reproducir:** `GET /api/v1/mediciones/inactividad` con alguna medición → `"ultima_medicion": "2026-09-11T00:00:00"`.
- **Arreglo sugerido:** Cambiar a `Optional[date]`.
- **Casos que fallan:** `ultima_medicion es una fecha YYYY-MM-DD`

## Observaciones para decidir en equipo

| ID | Tema | Detalle |
|---|---|---|
| O-01 | `GET /ejercicios` no pide login | Se pidió que **todos** los endpoints requieran login, pero `docs/api/api_01_ejercicios.md` define el catálogo como **público** (RN-38) y así está implementado. Si se exige login, agregar `Depends(get_current_user)` y actualizar RN-38 y la documentación. |
| O-02 | Sin límite de intentos de login | 25 contraseñas erradas seguidas y luego la correcta entra sin bloqueo ni `429`: fuerza bruta posible. Sugerido: rate limit por IP/correo (p. ej. `slowapi`). |
| O-03 | El access token sigue sirviendo después del logout | El logout revoca el refresh, pero el JWT de acceso vale hasta 15 min más. Es normal en JWT; si no se acepta, hay que tener lista de revocación o bajar la vida del token. |
| O-04 | Reusar un refresh viejo no revoca la sesión nueva | Si un refresh robado se reusa, se rechaza (bien), pero el token nuevo sigue vivo. Buena práctica: al detectar reuso, revocar todos los refresh del usuario. |
| O-05 | No hay fecha mínima en mediciones | Se aceptan `1900-01-01`, `1800-06-15`, `0001-01-01` y fechas anteriores al registro del usuario, en POST y en PUT. Definir regla (p. ej. no antes de 1900, o no antes de N años). |
| O-06 | Una fecha numérica se toma como timestamp | `"fecha": 1700000000` se guarda como `2023-11-14`. Un cliente con un bug enviaría una fecha errónea sin error. |
| O-07 | Conversión automática de tipos | `"peso_kg": "80"`, `"altura_cm": "175"` y `"consentimiento_datos": "true"` se aceptan. Con `strict=True` se rechazarían (ver H-09). |
| O-08 | Texto libre sin validar en el perfil | Se guardan tal cual `<img src=x onerror=alert(1)>` en nombre, `javascript:alert(1)` en `foto_url` y cualquier valor en `sexo`. El frontend **debe escapar**; se sugiere validar `foto_url` como `HttpUrl` y `sexo` con una lista. |
| O-09 | Masa muscular mayor que el peso | `peso_kg: 70` con `masa_muscular_kg: 90` se acepta. ¿Validar masa ≤ peso? |
| O-10 | POST y PUT tratan la fecha distinto | El POST acepta `2026-01-01T10:00:00`; el PUT lo rechaza con 422. Además, fecha futura es 400 en POST y (si se arregla H-02) 422 en PUT. Unificar. |
| O-11 | `GET /ejercicios?grupo_muscular=` devuelve `[]` | Un filtro vacío filtra por cadena vacía en vez de ignorarse. Un frontend que envíe el parámetro vacío verá el catálogo vacío. |
| O-12 | Swagger y OpenAPI públicos | `/docs` y `/openapi.json` responden 200 sin login. Bien para desarrollo; en producción conviene ocultarlos (`docs_url=None`). |

## Detalle de todos los casos por endpoint

### GET /salud

4 casos · ✅ 2 · ❌ 0 · ⚠️ 2

| # | Estado | Caso | Esperado | Obtenido | Ref. | Nota |
|---:|:---:|---|---|---|---|---|
| 1 | ✅ | responde sin autenticación | 200 | 200 |  |  |
| 2 | ✅ | token basura no afecta el health check | 200 | 200 |  |  |
| 3 | ⚠️ | Swagger /docs expuesto públicamente | 404 | 200 | O-12 | Útil en desarrollo; en producción conviene ocultarlo |
| 4 | ⚠️ | /openapi.json expuesto públicamente | 404 | 200 | O-12 | Expone el mapa completo de la API |

### POST /auth/registro

39 casos · ✅ 37 · ❌ 0 · ⚠️ 2

| # | Estado | Caso | Esperado | Obtenido | Ref. | Nota |
|---:|:---:|---|---|---|---|---|
| 1 | ✅ | registro válido devuelve par de tokens | 201 | 201 |  |  |
| 2 | ✅ | expires_in = 900 s (15 min) | 900 | 900 |  |  |
| 3 | ✅ | BD: consentimiento + fecha + hash Argon2id (RN-22) | t\|t\|t | t\|t\|t |  |  |
| 4 | ✅ | BD: la contraseña en claro no se guarda | 0 | 0 |  |  |
| 5 | ✅ | correo duplicado | 409 | 409 |  |  |
| 6 | ✅ | duplicado en MAYÚSCULAS (RN-20) | 409 | 409 |  |  |
| 7 | ✅ | correo con espacios/mayúsculas se normaliza | 201 | 201 |  |  |
| 8 | ✅ | correo con +etiqueta | 201 | 201 |  |  |
| 9 | ✅ | correo inválido | 422 | 422 |  |  |
| 10 | ✅ | correo sin dominio | 422 | 422 |  |  |
| 11 | ✅ | correo con parte local de 65 caracteres | 422 | 422 |  |  |
| 12 | ✅ | correo inyección SQL | 422 | 422 |  |  |
| 13 | ✅ | correo null | 422 | 422 |  |  |
| 14 | ✅ | contraseña de 7 caracteres | 422 | 422 |  |  |
| 15 | ✅ | contraseña sin número | 422 | 422 |  |  |
| 16 | ✅ | contraseña sin letra | 422 | 422 |  |  |
| 17 | ✅ | contraseña de 129 caracteres | 422 | 422 |  |  |
| 18 | ✅ | contraseña de 8 espacios | 422 | 422 |  |  |
| 19 | ✅ | contraseña número (no string) | 422 | 422 |  |  |
| 20 | ✅ | nombre vacío | 422 | 422 |  |  |
| 21 | ✅ | nombre solo espacios | 422 | 422 |  |  |
| 22 | ✅ | nombre de 101 caracteres | 422 | 422 |  |  |
| 23 | ✅ | consentimiento false | 422 | 422 |  |  |
| 24 | ✅ | consentimiento null | 422 | 422 |  |  |
| 25 | ✅ | sin campo consentimiento | 422 | 422 |  |  |
| 26 | ✅ | body vacío | 422 | 422 |  |  |
| 27 | ✅ | JSON malformado | 422 | 422 |  |  |
| 28 | ✅ | Content-Type text/plain | 422 | 422 |  | FastAPI no parsea JSON sin application/json |
| 29 | ✅ | el 422 no devuelve la contraseña (RN-22) | 422 | 422 |  |  |
| 30 | ✅ | contraseña de 8 exactos | 201 | 201 |  |  |
| 31 | ✅ | contraseña de 128 exactos | 201 | 201 |  |  |
| 32 | ✅ | contraseña con ñ y tildes | 201 | 201 |  |  |
| 33 | ✅ | nombre de 100 exactos | 201 | 201 |  |  |
| 34 | ✅ | nombre con tildes y emoji | 201 | 201 |  | Verificado por API: se guarda y devuelve igual (el fallo era de lectura de psql en Windows) |
| 35 | ✅ | nombre con espacios se recorta | 201 | 201 |  |  |
| 36 | ⚠️ | nombre con HTML/script se rechaza o sanea | 422 | 201 | O-08 | Se guarda tal cual; el frontend debe escapar |
| 37 | ⚠️ | consentimiento como string "true" se rechaza | 422 | 201 | O-07 | Pydantic lo convierte a bool |
| 38 | ✅ | asignación masiva (id, codigo_gimnasio, altura) ignorada | 201 | 201 |  |  |
| 39 | ✅ | 6 registros simultáneos mismo correo: 1×201 y 5×409, sin 500 | 1x201 5x409 | 1x201 5x409 |  |  |

### POST /auth/login

14 casos · ✅ 13 · ❌ 0 · ⚠️ 1

| # | Estado | Caso | Esperado | Obtenido | Ref. | Nota |
|---:|:---:|---|---|---|---|---|
| 1 | ✅ | login válido | 200 | 200 |  |  |
| 2 | ✅ | correo en MAYÚSCULAS | 200 | 200 |  |  |
| 3 | ✅ | correo con espacios | 200 | 200 |  |  |
| 4 | ✅ | contraseña con distinto uso de mayúsculas | 401 | 401 |  |  |
| 5 | ✅ | contraseña con espacio final | 401 | 401 |  |  |
| 6 | ✅ | contraseña incorrecta | 401 | 401 |  |  |
| 7 | ✅ | correo inexistente: mismo mensaje (RN-24) | 401 | 401 |  |  |
| 8 | ✅ | tiempo similar con correo existente e inexistente (RN-24) | True | True |  | 0.14s vs 0.14s |
| 9 | ✅ | inyección SQL en contraseña | 401 | 401 |  |  |
| 10 | ✅ | contraseña vacía | 422 | 422 |  |  |
| 11 | ✅ | sin contraseña | 422 | 422 |  |  |
| 12 | ✅ | contraseña de 129 | 422 | 422 |  |  |
| 13 | ✅ | correo inválido | 422 | 422 |  |  |
| 14 | ⚠️ | 25 intentos fallidos seguidos bloquean o limitan la cuenta | 429 | 200 | O-02 | No hay rate limit ni bloqueo: fuerza bruta posible |

### POST /auth/refresh

10 casos · ✅ 9 · ❌ 0 · ⚠️ 1

| # | Estado | Caso | Esperado | Obtenido | Ref. | Nota |
|---:|:---:|---|---|---|---|---|
| 1 | ✅ | refresh válido rota el token | 200 | 200 |  |  |
| 2 | ✅ | reusar refresh ya rotado | 401 | 401 |  |  |
| 3 | ⚠️ | tras detectar reuso se revoca toda la familia de tokens | 401 | 200 | O-04 | El token nuevo sigue vivo aunque se reusó el viejo (posible robo) |
| 4 | ✅ | access token usado como refresh | 401 | 401 |  |  |
| 5 | ✅ | token inventado | 401 | 401 |  |  |
| 6 | ✅ | inyección SQL | 401 | 401 |  |  |
| 7 | ✅ | token vacío | 422 | 422 |  |  |
| 8 | ✅ | sin token | 422 | 422 |  |  |
| 9 | ✅ | token de 100 KB | 401 | 401 |  |  |
| 10 | ✅ | refresh expirado | 401 | 401 |  |  |

### POST /auth/logout

7 casos · ✅ 6 · ❌ 0 · ⚠️ 1

| # | Estado | Caso | Esperado | Obtenido | Ref. | Nota |
|---:|:---:|---|---|---|---|---|
| 1 | ✅ | logout válido | 200 | 200 |  |  |
| 2 | ✅ | BD: refresh queda revocado | t | t |  |  |
| 3 | ✅ | refresh tras logout | 401 | 401 |  |  |
| 4 | ✅ | logout repetido: misma respuesta (RN-26) | 200 | 200 |  |  |
| 5 | ✅ | logout con token inventado (RN-26) | 200 | 200 |  |  |
| 6 | ✅ | logout token vacío | 422 | 422 |  |  |
| 7 | ⚠️ | el access token deja de servir tras logout | 401 | 200 | O-03 | JWT sigue válido hasta 15 min después del logout |

### GET /usuarios/me

18 casos · ✅ 18 · ❌ 0 · ⚠️ 0

| # | Estado | Caso | Esperado | Obtenido | Ref. | Nota |
|---:|:---:|---|---|---|---|---|
| 1 | ✅ | login requerido: sin header Authorization | 401 | 401 |  |  |
| 2 | ✅ | login requerido: Bearer vacío | 401 | 401 |  |  |
| 3 | ✅ | login requerido: esquema Basic | 401 | 401 |  |  |
| 4 | ✅ | login requerido: token sin esquema | 401 | 401 |  |  |
| 5 | ✅ | login requerido: token basura | 401 | 401 |  |  |
| 6 | ✅ | login requerido: token expirado | 401 | 401 |  |  |
| 7 | ✅ | login requerido: firmado con otro secreto | 401 | 401 |  |  |
| 8 | ✅ | login requerido: alg=none sin firma | 401 | 401 |  |  |
| 9 | ✅ | login requerido: payload manipulado (sub de otro usuario) | 401 | 401 |  |  |
| 10 | ✅ | login requerido: usuario inexistente | 401 | 401 |  |  |
| 11 | ✅ | login requerido: sub que no es UUID | 401 | 401 |  |  |
| 12 | ✅ | login requerido: sin claim exp | 401 | 401 |  |  |
| 13 | ✅ | login requerido: refresh token como access | 401 | 401 |  |  |
| 14 | ✅ | con token válido y esquema 'bearer' en minúsculas pasa el login | True | True |  | HTTP 200 |
| 15 | ✅ | el ataque PUT sin login no cambió el nombre | True | True |  |  |
| 16 | ✅ | devuelve el perfil del dueño del token | 200 | 200 |  |  |
| 17 | ✅ | no expone hash_password, consentimiento ni fechas internas | True | True |  |  |
| 18 | ✅ | usuario B ve su propio perfil, no el de A | 200 | 200 |  |  |

### PUT /usuarios/me

44 casos · ✅ 37 · ❌ 3 · ⚠️ 4

| # | Estado | Caso | Esperado | Obtenido | Ref. | Nota |
|---:|:---:|---|---|---|---|---|
| 1 | ✅ | login requerido: sin header Authorization | 401 | 401 |  |  |
| 2 | ✅ | login requerido: Bearer vacío | 401 | 401 |  |  |
| 3 | ✅ | login requerido: esquema Basic | 401 | 401 |  |  |
| 4 | ✅ | login requerido: token sin esquema | 401 | 401 |  |  |
| 5 | ✅ | login requerido: token basura | 401 | 401 |  |  |
| 6 | ✅ | login requerido: token expirado | 401 | 401 |  |  |
| 7 | ✅ | login requerido: firmado con otro secreto | 401 | 401 |  |  |
| 8 | ✅ | login requerido: alg=none sin firma | 401 | 401 |  |  |
| 9 | ✅ | login requerido: payload manipulado (sub de otro usuario) | 401 | 401 |  |  |
| 10 | ✅ | login requerido: usuario inexistente | 401 | 401 |  |  |
| 11 | ✅ | login requerido: sub que no es UUID | 401 | 401 |  |  |
| 12 | ✅ | login requerido: sin claim exp | 401 | 401 |  |  |
| 13 | ✅ | login requerido: refresh token como access | 401 | 401 |  |  |
| 14 | ✅ | con token válido y esquema 'bearer' en minúsculas pasa el login | True | True |  | HTTP 200 |
| 15 | ✅ | edición completa válida | 200 | 200 |  |  |
| 16 | ✅ | body vacío no cambia nada | 200 | 200 |  |  |
| 17 | ✅ | parcial: solo sexo, resto intacto | 200 | 200 |  |  |
| 18 | ✅ | nombre de 1 carácter | 422 | 422 |  |  |
| 19 | ✅ | nombre de 2 caracteres | 200 | 200 |  |  |
| 20 | ✅ | nombre de 101 caracteres | 422 | 422 |  |  |
| 21 | ❌ | nombre null | 422 | 500 | H-06 | NOT NULL en BD |
| 22 | ❌ | nombre solo espacios | 422 | 200 | H-07 | el registro sí lo rechaza |
| 23 | ❌ | nombre con espacios alrededor se recorta | Ana |   Ana   | H-07 |  |
| 24 | ✅ | altura 50 (excluido) | 422 | 422 |  |  |
| 25 | ✅ | altura 51 | 200 | 200 |  |  |
| 26 | ✅ | altura 299 | 200 | 200 |  |  |
| 27 | ✅ | altura 300 (excluido) | 422 | 422 |  |  |
| 28 | ✅ | altura negativa | 422 | 422 |  |  |
| 29 | ✅ | altura decimal 175.5 | 422 | 422 |  |  |
| 30 | ✅ | altura texto | 422 | 422 |  |  |
| 31 | ⚠️ | altura como string "175" | 422 | 200 | O-07 | Pydantic convierte "175" a 175 |
| 32 | ✅ | altura null (borra la altura) | 200 | 200 |  |  |
| 33 | ✅ | sexo de 21 caracteres | 422 | 422 |  |  |
| 34 | ⚠️ | sexo con valor arbitrario "xyz" | 422 | 200 | O-08 | No hay lista de valores permitidos |
| 35 | ✅ | foto_url de 501 caracteres | 422 | 422 |  |  |
| 36 | ⚠️ | foto_url no es URL (javascript:) | 422 | 200 | O-08 | No valida formato URL |
| 37 | ✅ | preferencias como lista | 422 | 422 |  |  |
| 38 | ✅ | preferencias como string | 422 | 422 |  |  |
| 39 | ⚠️ | nombre con HTML/script | 422 | 200 | O-08 | Se guarda tal cual |
| 40 | ✅ | asignación masiva (correo, id, hash, consentimiento…) ignorada | e2e.a.1789610501@test.com\|t\|t\|t\|t | e2e.a.1789610501@test.com\|t\|t\|t\|t |  |  |
| 41 | ✅ | tras intentar cambiar hash, el login sigue igual | 200 | 200 |  |  |
| 42 | ✅ | los cambios de A no afectan a B | 200 | 200 |  |  |
| 43 | ✅ | PATCH no permitido | 405 | 405 |  |  |
| 44 | ✅ | DELETE no permitido | 405 | 405 |  |  |

### GET /ejercicios

20 casos · ✅ 17 · ❌ 0 · ⚠️ 3

| # | Estado | Caso | Esperado | Obtenido | Ref. | Nota |
|---:|:---:|---|---|---|---|---|
| 1 | ⚠️ | login requerido: sin header Authorization | 401 | 200 | O-01 | Público por diseño (RN-38 en docs); se pidió login en todos los endpoints |
| 2 | ⚠️ | login requerido: token basura | 401 | 200 | O-01 | Público por diseño (RN-38 en docs); se pidió login en todos los endpoints |
| 3 | ✅ | con login devuelve los 41 activos | 200 | 200 |  |  |
| 4 | ✅ | no incluye inactivos (RN-39) | True | True |  |  |
| 5 | ✅ | no expone el campo activo | True | True |  |  |
| 6 | ✅ | orden por grupo_muscular y nombre_es | True | True |  |  |
| 7 | ✅ | filtro grupo_muscular=pecho | 200 | 200 |  | 6 de 6 |
| 8 | ✅ | filtro equipo=barra | 200 | 200 |  | 8 de 8 |
| 9 | ✅ | filtro categoria=cardio | 200 | 200 |  | 2 de 2 |
| 10 | ✅ | filtro con MAYÚSCULAS y espacios | 200 | 200 |  | 6 de 6 |
| 11 | ✅ | tres filtros combinados (AND) | 200 | 200 |  | 2 de 2 |
| 12 | ✅ | valor inexistente → [] | 200 | 200 |  | 0 de 0 |
| 13 | ✅ | inyección SQL en filtro | 200 | 200 |  | 0 de 0 |
| 14 | ✅ | filtro de 10.000 caracteres | 200 | 200 |  | 0 de 0 |
| 15 | ✅ | parámetro desconocido se ignora | 200 | 200 |  | 41 de 41 |
| 16 | ✅ | parámetro repetido usa el último | 200 | 200 |  | 7 de 7 |
| 17 | ⚠️ | filtro vacío (?grupo_muscular=) devuelve todo | 200 | 200 | O-11 | Devuelve [] porque filtra por grupo_muscular = '' |
| 18 | ✅ | POST no permitido (RN-38) | 405 | 405 |  |  |
| 19 | ✅ | PUT no permitido (RN-38) | 405 | 405 |  |  |
| 20 | ✅ | DELETE no permitido (RN-38) | 405 | 405 |  |  |

### POST /mediciones

74 casos · ✅ 56 · ❌ 11 · ⚠️ 7

| # | Estado | Caso | Esperado | Obtenido | Ref. | Nota |
|---:|:---:|---|---|---|---|---|
| 1 | ✅ | login requerido: sin header Authorization | 401 | 401 |  |  |
| 2 | ✅ | login requerido: Bearer vacío | 401 | 401 |  |  |
| 3 | ✅ | login requerido: esquema Basic | 401 | 401 |  |  |
| 4 | ✅ | login requerido: token sin esquema | 401 | 401 |  |  |
| 5 | ✅ | login requerido: token basura | 401 | 401 |  |  |
| 6 | ✅ | login requerido: token expirado | 401 | 401 |  |  |
| 7 | ✅ | login requerido: firmado con otro secreto | 401 | 401 |  |  |
| 8 | ✅ | login requerido: alg=none sin firma | 401 | 401 |  |  |
| 9 | ✅ | login requerido: payload manipulado (sub de otro usuario) | 401 | 401 |  |  |
| 10 | ✅ | login requerido: usuario inexistente | 401 | 401 |  |  |
| 11 | ✅ | login requerido: sub que no es UUID | 401 | 401 |  |  |
| 12 | ✅ | login requerido: sin claim exp | 401 | 401 |  |  |
| 13 | ✅ | login requerido: refresh token como access | 401 | 401 |  |  |
| 14 | ✅ | con token válido y esquema 'bearer' en minúsculas pasa el login | True | True |  | HTTP 201 |
| 15 | ✅ | medición completa hace 40 días | 201 | 201 |  | IMC 80/1.75² = 26.1 |
| 16 | ✅ | segunda medición el mismo día | 201 | 201 |  | No hay regla de una por día |
| 17 | ✅ | solo obligatorios + grasa | 201 | 201 |  |  |
| 18 | ✅ | usuario_id ajeno en el body se ignora | 201 | 201 |  |  |
| 19 | ✅ | hoy (Colombia) con zona -05:00 | 201 | 201 |  |  |
| 20 | ✅ | hoy (Colombia) sin hora | 201 | 201 |  |  |
| 21 | ✅ | RN-70: fecha futura +2 días | 400 | 400 |  |  |
| 22 | ✅ | RN-70: fecha futura +1 hora (UTC) | 400 | 400 |  |  |
| 23 | ✅ | RN-70: fecha 9999-12-31 | 400 | 400 |  |  |
| 24 | ❌ | RN-70: mañana en Colombia (2026-09-17) sin zona | 400 | 201 | H-05 | UTC hoy=2026-09-17; Colombia hoy=2026-09-16. Solo falla de 7 p. m. a medianoche |
| 25 | ✅ | fecha anterior: hace 1 año | 201 | 201 |  |  |
| 26 | ✅ | fecha anterior: hace 10 años | 201 | 201 |  |  |
| 27 | ✅ | fecha anterior: 1990-01-01 | 201 | 201 |  |  |
| 28 | ⚠️ | fecha anterior absurda: 1900-01-01 se rechaza | 422 | 201 | O-05 | Se acepta: no hay fecha mínima |
| 29 | ⚠️ | fecha anterior absurda: 1800-06-15 se rechaza | 422 | 201 | O-05 | Se acepta: no hay fecha mínima |
| 30 | ⚠️ | fecha anterior absurda: 0001-01-01 (año 1) se rechaza | 422 | 201 | O-05 | Se acepta: no hay fecha mínima |
| 31 | ⚠️ | fecha anterior al registro del usuario (2026-09-16) se rechaza | 422 | 201 | O-05 | Se acepta: ¿se permite cargar historial previo? |
| 32 | ✅ | fecha inválida: 2025-02-29 (no bisiesto) | 422 | 422 |  |  |
| 33 | ✅ | fecha inválida: 2026-13-01 (mes 13) | 422 | 422 |  |  |
| 34 | ✅ | fecha inválida: 2026-04-31 (día 31 en abril) | 422 | 422 |  |  |
| 35 | ✅ | fecha inválida: 2026-09-00 | 422 | 422 |  |  |
| 36 | ✅ | fecha inválida: formato DD-MM-YYYY | 422 | 422 |  |  |
| 37 | ✅ | fecha inválida: formato DD/MM/YYYY | 422 | 422 |  |  |
| 38 | ✅ | fecha inválida: hora 25:00 | 422 | 422 |  |  |
| 39 | ✅ | fecha inválida: texto | 422 | 422 |  |  |
| 40 | ✅ | fecha inválida: vacía | 422 | 422 |  |  |
| 41 | ✅ | fecha inválida: null | 422 | 422 |  |  |
| 42 | ✅ | fecha 2024-02-29 (bisiesto) | 201 | 201 |  |  |
| 43 | ⚠️ | fecha como número (timestamp) se rechaza | 422 | 201 | O-06 | Se acepta como timestamp Unix → 2023-11-14 |
| 44 | ✅ | sin fecha | 422 | 422 |  |  |
| 45 | ✅ | peso 0 (RN-03) | 422 | 422 |  |  |
| 46 | ✅ | peso negativo | 422 | 422 |  |  |
| 47 | ❌ | peso 0.001 (se guardaría 0.00) | 422 | 201 | H-08 | Pasa gt=0 pero NUMERIC(5,2) lo redondea a 0.00 → rompe RN-03 |
| 48 | ✅ | peso 999.99 (tope de columna) | 201 | 201 |  |  |
| 49 | ❌ | peso 1000 (excede NUMERIC(5,2)) | 422 | 500 | H-01 | El PUT sí tiene le=999.99 |
| 50 | ❌ | peso 1e308 | 422 | 500 | H-01 |  |
| 51 | ✅ | peso texto | 422 | 422 |  |  |
| 52 | ⚠️ | peso como string "80" | 422 | 201 | O-07 | Pydantic convierte "80" a 80 |
| 53 | ❌ | peso booleano true | 422 | 201 | H-09 |  |
| 54 | ✅ | peso lista | 422 | 422 |  |  |
| 55 | ✅ | peso null | 422 | 422 |  |  |
| 56 | ✅ | grasa 0 (RN-04) | 201 | 201 |  |  |
| 57 | ✅ | grasa 100 (RN-04) | 201 | 201 |  |  |
| 58 | ✅ | grasa -0.01 | 422 | 422 |  |  |
| 59 | ✅ | grasa 100.01 | 422 | 422 |  |  |
| 60 | ✅ | masa muscular 0 (RN-05) | 422 | 422 |  |  |
| 61 | ❌ | masa muscular 1000 | 422 | 500 | H-01 |  |
| 62 | ⚠️ | masa muscular mayor que el peso | 422 | 201 | O-09 | No se valida masa ≤ peso |
| 63 | ✅ | cintura 0 (RN-06) | 422 | 422 |  |  |
| 64 | ✅ | cadera negativa (RN-06) | 422 | 422 |  |  |
| 65 | ❌ | brazo 1000 | 422 | 500 | H-01 |  |
| 66 | ❌ | pierna 1000 | 422 | 500 | H-01 |  |
| 67 | ❌ | pecho 1000 | 422 | 500 | H-01 |  |
| 68 | ❌ | cintura 1000 | 422 | 500 | H-01 |  |
| 69 | ✅ | decimales extra se redondean a 2 (70.555 → 70.56) | 201 | 201 |  | guardado 70.56 |
| 70 | ❌ | peso Infinity | 422 | 500 | H-01 |  |
| 71 | ✅ | peso NaN | 422 | 422 |  |  |
| 72 | ✅ | body vacío | 422 | 422 |  |  |
| 73 | ✅ | body lista | 422 | 422 |  |  |
| 74 | ✅ | usuario B sin altura → imc null | 201 | 201 |  |  |

### GET /mediciones

30 casos · ✅ 30 · ❌ 0 · ⚠️ 0

| # | Estado | Caso | Esperado | Obtenido | Ref. | Nota |
|---:|:---:|---|---|---|---|---|
| 1 | ✅ | login requerido: sin header Authorization | 401 | 401 |  |  |
| 2 | ✅ | login requerido: Bearer vacío | 401 | 401 |  |  |
| 3 | ✅ | login requerido: esquema Basic | 401 | 401 |  |  |
| 4 | ✅ | login requerido: token sin esquema | 401 | 401 |  |  |
| 5 | ✅ | login requerido: token basura | 401 | 401 |  |  |
| 6 | ✅ | login requerido: token expirado | 401 | 401 |  |  |
| 7 | ✅ | login requerido: firmado con otro secreto | 401 | 401 |  |  |
| 8 | ✅ | login requerido: alg=none sin firma | 401 | 401 |  |  |
| 9 | ✅ | login requerido: payload manipulado (sub de otro usuario) | 401 | 401 |  |  |
| 10 | ✅ | login requerido: usuario inexistente | 401 | 401 |  |  |
| 11 | ✅ | login requerido: sub que no es UUID | 401 | 401 |  |  |
| 12 | ✅ | login requerido: sin claim exp | 401 | 401 |  |  |
| 13 | ✅ | login requerido: refresh token como access | 401 | 401 |  |  |
| 14 | ✅ | con token válido y esquema 'bearer' en minúsculas pasa el login | True | True |  | HTTP 200 |
| 15 | ✅ | solo las 4 mediciones propias | 200 | 200 |  | 4 filas |
| 16 | ✅ | orden cronológico ascendente | True | True |  |  |
| 17 | ✅ | cada fila trae imc calculado | True | True |  |  |
| 18 | ✅ | desde/hasta inclusivos | 200 | 200 |  | 2 de 2 |
| 19 | ✅ | desde == hasta | 200 | 200 |  | 1 de 1 |
| 20 | ✅ | solo desde | 200 | 200 |  | 2 de 2 |
| 21 | ✅ | solo hasta | 200 | 200 |  | 3 de 3 |
| 22 | ✅ | rango 0001-01-01 a 9999-12-31 | 200 | 200 |  | 4 de 4 |
| 23 | ✅ | rango sin resultados | 200 | 200 |  | 0 de 0 |
| 24 | ✅ | rango en el futuro | 200 | 200 |  | 0 de 0 |
| 25 | ✅ | desde > hasta | 422 | 422 |  |  |
| 26 | ✅ | desde texto | 422 | 422 |  |  |
| 27 | ✅ | hasta 2026-02-30 | 422 | 422 |  |  |
| 28 | ✅ | desde con hora | 422 | 422 |  |  |
| 29 | ✅ | B no ve mediciones de A (RN-08) | 200 | 200 |  |  |
| 30 | ✅ | ?usuario_id=A con token de B se ignora | 200 | 200 |  |  |

### GET /mediciones/{id}

21 casos · ✅ 21 · ❌ 0 · ⚠️ 0

| # | Estado | Caso | Esperado | Obtenido | Ref. | Nota |
|---:|:---:|---|---|---|---|---|
| 1 | ✅ | login requerido: sin header Authorization | 401 | 401 |  |  |
| 2 | ✅ | login requerido: Bearer vacío | 401 | 401 |  |  |
| 3 | ✅ | login requerido: esquema Basic | 401 | 401 |  |  |
| 4 | ✅ | login requerido: token sin esquema | 401 | 401 |  |  |
| 5 | ✅ | login requerido: token basura | 401 | 401 |  |  |
| 6 | ✅ | login requerido: token expirado | 401 | 401 |  |  |
| 7 | ✅ | login requerido: firmado con otro secreto | 401 | 401 |  |  |
| 8 | ✅ | login requerido: alg=none sin firma | 401 | 401 |  |  |
| 9 | ✅ | login requerido: payload manipulado (sub de otro usuario) | 401 | 401 |  |  |
| 10 | ✅ | login requerido: usuario inexistente | 401 | 401 |  |  |
| 11 | ✅ | login requerido: sub que no es UUID | 401 | 401 |  |  |
| 12 | ✅ | login requerido: sin claim exp | 401 | 401 |  |  |
| 13 | ✅ | login requerido: refresh token como access | 401 | 401 |  |  |
| 14 | ✅ | con token válido y esquema 'bearer' en minúsculas pasa el login | True | True |  | HTTP 404 |
| 15 | ✅ | detalle propio | 200 | 200 |  |  |
| 16 | ✅ | detalle ajeno → 404 (RN-08) | 404 | 404 |  |  |
| 17 | ✅ | UUID inexistente | 404 | 404 |  |  |
| 18 | ✅ | id no UUID | 422 | 422 |  |  |
| 19 | ✅ | id numérico | 422 | 422 |  |  |
| 20 | ✅ | inyección SQL | 422 | 422 |  |  |
| 21 | ✅ | UUID en mayúsculas | 200 | 200 |  |  |

### PUT /mediciones/{id}

41 casos · ✅ 35 · ❌ 3 · ⚠️ 3

| # | Estado | Caso | Esperado | Obtenido | Ref. | Nota |
|---:|:---:|---|---|---|---|---|
| 1 | ✅ | login requerido: sin header Authorization | 401 | 401 |  |  |
| 2 | ✅ | login requerido: Bearer vacío | 401 | 401 |  |  |
| 3 | ✅ | login requerido: esquema Basic | 401 | 401 |  |  |
| 4 | ✅ | login requerido: token sin esquema | 401 | 401 |  |  |
| 5 | ✅ | login requerido: token basura | 401 | 401 |  |  |
| 6 | ✅ | login requerido: token expirado | 401 | 401 |  |  |
| 7 | ✅ | login requerido: firmado con otro secreto | 401 | 401 |  |  |
| 8 | ✅ | login requerido: alg=none sin firma | 401 | 401 |  |  |
| 9 | ✅ | login requerido: payload manipulado (sub de otro usuario) | 401 | 401 |  |  |
| 10 | ✅ | login requerido: usuario inexistente | 401 | 401 |  |  |
| 11 | ✅ | login requerido: sub que no es UUID | 401 | 401 |  |  |
| 12 | ✅ | login requerido: sin claim exp | 401 | 401 |  |  |
| 13 | ✅ | login requerido: refresh token como access | 401 | 401 |  |  |
| 14 | ✅ | con token válido y esquema 'bearer' en minúsculas pasa el login | True | True |  | HTTP 404 |
| 15 | ✅ | parcial: solo peso, resto intacto, IMC recalculado | 200 | 200 |  |  |
| 16 | ✅ | null en obligatorios (peso, fecha) se ignora | 200 | 200 |  |  |
| 17 | ✅ | null en opcional lo vacía | 200 | 200 |  |  |
| 18 | ✅ | usuario_id / id / creado_en en body se ignoran (RN-37) | 200 | 200 |  |  |
| 19 | ✅ | body vacío | 200 | 200 |  |  |
| 20 | ✅ | peso 999.99 | 200 | 200 |  |  |
| 21 | ✅ | peso 1000 | 422 | 422 |  |  |
| 22 | ✅ | peso 0 | 422 | 422 |  |  |
| 23 | ❌ | peso 0.001 (se guardaría 0.00) | 422 | 200 | H-08 | NUMERIC(5,2) lo redondea a 0.00 → rompe RN-03 |
| 24 | ✅ | grasa 100 | 200 | 200 |  |  |
| 25 | ✅ | grasa 100.01 | 422 | 422 |  |  |
| 26 | ✅ | grasa -1 | 422 | 422 |  |  |
| 27 | ✅ | masa 0 | 422 | 422 |  |  |
| 28 | ✅ | brazo 1000 | 422 | 422 |  |  |
| 29 | ✅ | peso texto | 422 | 422 |  |  |
| 30 | ❌ | fecha futura +3 días (RN-70) | 422 | 200 | H-02 | El POST la rechaza con 400 |
| 31 | ❌ | fecha 9999-12-31 (RN-70) | 422 | 200 | H-02 |  |
| 32 | ⚠️ | fecha 1900-01-01 | 422 | 200 | O-05 | Se acepta: no hay fecha mínima |
| 33 | ⚠️ | fecha 0001-01-01 | 422 | 200 | O-05 | Se acepta: no hay fecha mínima |
| 34 | ⚠️ | fecha con hora 10:00 (el POST sí la acepta) | 200 | 422 | O-10 | Inconsistente con POST |
| 35 | ✅ | fecha 2025-02-29 | 422 | 422 |  |  |
| 36 | ✅ | fecha texto | 422 | 422 |  |  |
| 37 | ✅ | medición ajena → 404 (RN-08) | 404 | 404 |  |  |
| 38 | ✅ | BD: la medición ajena no cambió | 76.00 | 76.00 |  |  |
| 39 | ✅ | UUID inexistente | 404 | 404 |  |  |
| 40 | ✅ | id no UUID | 422 | 422 |  |  |
| 41 | ✅ | PATCH no permitido | 405 | 405 |  |  |

### DELETE /mediciones/{id}

24 casos · ✅ 24 · ❌ 0 · ⚠️ 0

| # | Estado | Caso | Esperado | Obtenido | Ref. | Nota |
|---:|:---:|---|---|---|---|---|
| 1 | ✅ | login requerido: sin header Authorization | 401 | 401 |  |  |
| 2 | ✅ | login requerido: Bearer vacío | 401 | 401 |  |  |
| 3 | ✅ | login requerido: esquema Basic | 401 | 401 |  |  |
| 4 | ✅ | login requerido: token sin esquema | 401 | 401 |  |  |
| 5 | ✅ | login requerido: token basura | 401 | 401 |  |  |
| 6 | ✅ | login requerido: token expirado | 401 | 401 |  |  |
| 7 | ✅ | login requerido: firmado con otro secreto | 401 | 401 |  |  |
| 8 | ✅ | login requerido: alg=none sin firma | 401 | 401 |  |  |
| 9 | ✅ | login requerido: payload manipulado (sub de otro usuario) | 401 | 401 |  |  |
| 10 | ✅ | login requerido: usuario inexistente | 401 | 401 |  |  |
| 11 | ✅ | login requerido: sub que no es UUID | 401 | 401 |  |  |
| 12 | ✅ | login requerido: sin claim exp | 401 | 401 |  |  |
| 13 | ✅ | login requerido: refresh token como access | 401 | 401 |  |  |
| 14 | ✅ | con token válido y esquema 'bearer' en minúsculas pasa el login | True | True |  | HTTP 404 |
| 15 | ✅ | medición ajena → 404 (RN-08) | 404 | 404 |  |  |
| 16 | ✅ | BD: la medición ajena sigue existiendo | 1 | 1 |  |  |
| 17 | ✅ | medición propia | 204 | 204 |  |  |
| 18 | ✅ | borrar dos veces → 404 | 404 | 404 |  |  |
| 19 | ✅ | GET tras borrar → 404 | 404 | 404 |  |  |
| 20 | ✅ | BD: borrado físico (RN-36) | 0 | 0 |  |  |
| 21 | ✅ | UUID inexistente | 404 | 404 |  |  |
| 22 | ✅ | id no UUID | 422 | 422 |  |  |
| 23 | ✅ | DELETE sobre la colección no permitido | 405 | 405 |  |  |
| 24 | ✅ | las mediciones de B siguen intactas | 200 | 200 |  |  |

### GET /mediciones/inactividad

24 casos · ✅ 16 · ❌ 8 · ⚠️ 0

| # | Estado | Caso | Esperado | Obtenido | Ref. | Nota |
|---:|:---:|---|---|---|---|---|
| 1 | ✅ | login requerido: sin header Authorization | 401 | 401 |  |  |
| 2 | ✅ | login requerido: Bearer vacío | 401 | 401 |  |  |
| 3 | ✅ | login requerido: esquema Basic | 401 | 401 |  |  |
| 4 | ✅ | login requerido: token sin esquema | 401 | 401 |  |  |
| 5 | ✅ | login requerido: token basura | 401 | 401 |  |  |
| 6 | ✅ | login requerido: token expirado | 401 | 401 |  |  |
| 7 | ✅ | login requerido: firmado con otro secreto | 401 | 401 |  |  |
| 8 | ✅ | login requerido: alg=none sin firma | 401 | 401 |  |  |
| 9 | ✅ | login requerido: payload manipulado (sub de otro usuario) | 401 | 401 |  |  |
| 10 | ✅ | login requerido: usuario inexistente | 401 | 401 |  |  |
| 11 | ✅ | login requerido: sub que no es UUID | 401 | 401 |  |  |
| 12 | ✅ | login requerido: sin claim exp | 401 | 401 |  |  |
| 13 | ✅ | login requerido: refresh token como access | 401 | 401 |  |  |
| 14 | ✅ | con token válido y esquema 'bearer' en minúsculas pasa el login | True | True |  | HTTP 200 |
| 15 | ❌ | con una medición futura (colada por PUT) los días no son negativos | True | False | H-03 | dias_desde_ultima_medicion = -2912183 |
| 16 | ❌ | última hace 5 días → activo | 200 | 200 | H-05 | días = 6 (hoy Colombia 2026-09-16, UTC 2026-09-17) |
| 17 | ❌ | ultima_medicion es una fecha YYYY-MM-DD | 2026-09-11 | 2026-09-11T00:00:00 | H-10 | Devuelve datetime con T00:00:00 |
| 18 | ✅ | sin mediciones → nulls y false | 200 | 200 |  |  |
| 19 | ❌ | última hace 0 días → esta_inactivo=False | 200 | 200 | H-05 | días = 1 |
| 20 | ❌ | última hace 29 días → esta_inactivo=False | 200 | 200 | H-05 | días = 30 |
| 21 | ❌ | última hace 30 días → esta_inactivo=True | 200 | 200 | H-05 | días = 31 |
| 22 | ❌ | última hace 31 días → esta_inactivo=True | 200 | 200 | H-05 | días = 32 |
| 23 | ❌ | última hace 400 días → esta_inactivo=True | 200 | 200 | H-05 | días = 401 |
| 24 | ✅ | con varias mediciones toma la más reciente (no la última creada) | 200 | 200 |  |  |

### GET /mediciones/comparar

26 casos · ✅ 25 · ❌ 1 · ⚠️ 0

| # | Estado | Caso | Esperado | Obtenido | Ref. | Nota |
|---:|:---:|---|---|---|---|---|
| 1 | ✅ | login requerido: sin header Authorization | 401 | 401 |  |  |
| 2 | ✅ | login requerido: Bearer vacío | 401 | 401 |  |  |
| 3 | ✅ | login requerido: esquema Basic | 401 | 401 |  |  |
| 4 | ✅ | login requerido: token sin esquema | 401 | 401 |  |  |
| 5 | ✅ | login requerido: token basura | 401 | 401 |  |  |
| 6 | ✅ | login requerido: token expirado | 401 | 401 |  |  |
| 7 | ✅ | login requerido: firmado con otro secreto | 401 | 401 |  |  |
| 8 | ✅ | login requerido: alg=none sin firma | 401 | 401 |  |  |
| 9 | ✅ | login requerido: payload manipulado (sub de otro usuario) | 401 | 401 |  |  |
| 10 | ✅ | login requerido: usuario inexistente | 401 | 401 |  |  |
| 11 | ✅ | login requerido: sub que no es UUID | 401 | 401 |  |  |
| 12 | ✅ | login requerido: sin claim exp | 401 | 401 |  |  |
| 13 | ✅ | login requerido: refresh token como access | 401 | 401 |  |  |
| 14 | ✅ | con token válido y esquema 'bearer' en minúsculas pasa el login | True | True |  | HTTP 404 |
| 15 | ✅ | diferencias = reciente − anterior | 200 | 200 |  | 76 → 70 kg = −6; IMC 24.8 → 22.9 = −1.9 |
| 16 | ✅ | fechas invertidas → mismo resultado | 200 | 200 |  |  |
| 17 | ✅ | misma fecha | 400 | 400 |  |  |
| 18 | ✅ | falta fecha2 | 422 | 422 |  |  |
| 19 | ✅ | sin parámetros | 422 | 422 |  |  |
| 20 | ✅ | fecha2 texto | 422 | 422 |  |  |
| 21 | ✅ | fecha2 inexistente (30 feb) | 422 | 422 |  |  |
| 22 | ✅ | una fecha sin medición | 404 | 404 |  |  |
| 23 | ✅ | fechas extremas sin mediciones | 404 | 404 |  |  |
| 24 | ✅ | fechas con mediciones de otro usuario → 404 | 404 | 404 |  |  |
| 25 | ❌ | fecha con 2 mediciones el mismo día | 200 | 500 | H-04 | La API permite varias mediciones por día |
| 26 | ✅ | sin altura: imc y diferencia de imc en null | 200 | 200 |  |  |

### Cuenta eliminada

4 casos · ✅ 4 · ❌ 0 · ⚠️ 0

| # | Estado | Caso | Esperado | Obtenido | Ref. | Nota |
|---:|:---:|---|---|---|---|---|
| 1 | ✅ | access token de cuenta borrada | 401 | 401 |  |  |
| 2 | ✅ | refresh de cuenta borrada | 401 | 401 |  |  |
| 3 | ✅ | login de cuenta borrada | 401 | 401 |  |  |
| 4 | ✅ | mediciones y refresh tokens borrados en cascada | 0\|0 | 0\|0 |  |  |

## Recomendación

**No unir `dev` a `main` todavía.** Antes hay que corregir los hallazgos de severidad alta: H-01, H-02 (con H-03), H-04 y H-06. Después se vuelve a correr la batería completa sobre `dev`.
Las observaciones (O-xx) no bloquean el merge, pero conviene decidirlas y convertirlas en reglas de negocio o en tareas.
