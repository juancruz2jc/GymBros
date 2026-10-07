# API · Sesiones de entrenamiento

Estado: **RF-15 (iniciar)** · **RF-17 (finalizar)** · **RN-68 (descartar /
reanudar)** · **RF-18 (calificar)** implementados. RF-16 (registrar series):
pendiente de integrar (rama de GYM-16).
Base URL local: `http://localhost:8001` · Prefijo: `/api/v1` · Todos los
endpoints requieren `Authorization: Bearer <access_token>`.

---

## Ciclo de vida de una sesión

```
POST /sesiones ──► ACTIVA ──► POST /sesiones/{id}/finalizar ──► FINALIZADA ──► PATCH /sesiones/{id}/calificacion
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

## Reglas de negocio aplicadas

| Regla | Dónde |
|---|---|
| RN-44 · una sola sesión activa | `sesion_service.iniciar_sesion` → `SesionActivaExistenteError` → 409 |
| RN-47 · duración automática, no se finaliza dos veces | `finalizar_sesion` |
| RN-48 · calificación opcional | `PATCH …/calificacion` aparte del cierre |
| RN-60 · solo el dueño | todas las consultas filtran `usuario_id` del token en el `WHERE`; ajena = 404, igual que inexistente |
| RN-67 · idempotencia offline | `idempotency_key` (restricción única); reintento → 200 con la misma sesión; primer cierre gana |
| RN-68 · descartar / reanudar | `DELETE /sesiones/{id}` y `GET /sesiones/activa` |
| RN-69 · finalizar vacía con advertencia | `confirmar_sin_series` |

## Pendiente / fuera de este alcance

- **RN-56 (racha y logros al finalizar):** RF-23/RF-24 son del siguiente
  sprint. Cuando se implementen, se evalúan dentro de `finalizar_sesion`.
- **RN-44 con peticiones simultáneas:** se valida consultando antes de
  insertar. Dos inicios **simultáneos con claves distintas** podrían crear dos
  sesiones activas; la solución completa es un índice único parcial
  (`usuario_id WHERE finalizada_en IS NULL`), que requiere migración.
- **RF-19 (historial de entrenamientos):** no hay listado de sesiones pasadas
  todavía.

## Casos de prueba

Ejecutados contra Supabase el 2026-10-07 con dos usuarios de prueba (borrados
al final). Rutina y series insertadas directo en la base porque rutinas
(GYM-149) y series (GYM-16) aún no están en `dev`. **Los 25 pasan.**

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
