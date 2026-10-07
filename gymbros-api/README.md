# GymBros API

Backend de GymBros: FastAPI + PostgreSQL. La base de datos es **una sola,
compartida por todo el equipo, en Supabase**: nadie levanta un PostgreSQL
propio.

---

## Levantar el proyecto

Hay dos modos. **Docker es el recomendado** — te da Python con la versión
correcta sin instalar nada. El modo venv existe para quien no pueda usar
Docker. Los dos se conectan a la misma base de Supabase.

### Paso común: crear tu `.env`

El `.env` no está en el repositorio porque contiene secretos. Cada quien
crea el suyo a partir de la plantilla:

```powershell
Copy-Item .env.example .env
```

En tu `.env`:

1. En `DATABASE_URL`, reemplaza `[CONTRASEÑA_DE_SUPABASE]` por la contraseña
   de la base (pídela al equipo; **nunca** la subas al repo ni la pegues en el
   chat). Si tiene caracteres especiales, codifícalos como indica el
   `.env.example`.
2. Genera un secreto real y pégalo en `JWT_SECRET`:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**La app no arranca si dejas el valor de ejemplo.** Es a propósito: un
secreto que está escrito en el repositorio no es un secreto. Lo mismo si
falta `DATABASE_URL` o `JWT_SECRET` — mejor un error al arrancar que un
problema silencioso.

---

### Modo A — Docker (recomendado)

Desde la **raíz del monorepo**, no desde esta carpeta:

```powershell
docker compose up --build
```

El `--build` solo hace falta la primera vez o cuando cambie el
`Dockerfile` o el `requirements.txt`. El resto de las veces:

```powershell
docker compose up
```

---

### Modo B — Local con venv

```powershell
cd gymbros-api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Para arrancar:

```powershell
uvicorn app.main:app --reload --port 8001
```

---

## Verificar que funciona

| Qué | URL |
|---|---|
| Comprobación de vida | http://localhost:8001/salud |
| Swagger (documentación y pruebas) | http://localhost:8001/docs |

> El puerto es **8001**, no 8000. Se cambió porque el 8000 suele estar
> ocupado por otros proyectos. Si en Windows `localhost` corta la conexión,
> usa `127.0.0.1:8001` (Docker Desktop a veces falla por IPv6).

`/docs` es el banco de pruebas del sprint: lista todos los endpoints y
permite ejecutarlos desde el navegador. No hay que configurarlo — se
genera solo a partir de las anotaciones de tipos del código.

---

## Comandos útiles

| Qué quieres | Comando |
|---|---|
| Levantar | `docker compose up` |
| Apagar | `docker compose down` |
| Ver los logs de la API | `docker compose logs -f api` |
| Terminal dentro del contenedor | `docker compose exec api sh` (la imagen es Alpine: no trae `bash`) |
| Ver en qué migración está la base | `docker compose exec api alembic current` |
| Aplicar migraciones | `docker compose exec api alembic upgrade head` (ver reglas abajo) |

Los cambios en archivos `.py` se recargan solos: el código está montado
como volumen y uvicorn corre con `--reload`.

### Reglas de la base compartida

Todo el equipo trabaja sobre la misma base, así que lo que hace uno lo ven
todos:

- **Solo se aplican migraciones que ya están en `dev`.** Una migración de una
  rama sin mergear deja la base adelantada respecto al código de los demás:
  su `alembic current` y `alembic upgrade` fallan con
  `Can't locate revision` y el esquema deja de coincidir con sus modelos.
- Antes de migrar, revisa en qué revisión está: `alembic current`. Avisa al
  grupo antes de aplicar una migración.
- No borres datos que no creaste tú. Los datos de prueba se crean con
  correos que se reconozcan como tuyos (p. ej. `juan+prueba1@...`).

---

## Datos de ejemplo (seeds)

Scripts de una sola vez que se corren **a mano** tras aplicar las migraciones.
No son parte del arranque de la API.

### Catálogo de ejercicios (`scripts/seed_ejercicios.py`)

Carga un set de maquetado (43 ejercicios: 41 activos + 2 inactivos, repartidos
entre 10 grupos musculares, 6 equipos y 5 categorías) para poder probar los filtros de
`GET /api/v1/ejercicios`. Incluye a propósito dos ejercicios con
`activo = false` para verificar que el catálogo público los oculta (RN-39).
Es **idempotente**: identifica cada fila por `nombre_en` y solo inserta lo que
falta, así que se puede repetir sin duplicar. **En Supabase ya está cargado**:
solo hace falta volver a correrlo si se agregan ejercicios al script.

```powershell
# Con Docker, desde la raíz del monorepo
docker compose exec api python -m scripts.seed_ejercicios

# En local (venv), desde gymbros-api/
python -m scripts.seed_ejercicios
```

No es el catálogo definitivo: RF-12 prevé migrar a una fuente con licencia
clara (wger) más adelante; las `gif_url` de este seed son marcadores de
posición.

---

## Estructura de carpetas

```
gymbros-api/
├── Dockerfile             cómo se construye la imagen de este servicio
├── requirements.txt       dependencias con versiones fijadas
├── .env.example           plantilla de variables de entorno
├── alembic.ini            configuración de las migraciones
│
├── alembic/               migraciones versionadas del esquema
│   └── versions/          una migración por cambio, en orden
│
├── scripts/               tareas de una sola vez (seeds), se corren a mano
├── tests/                 pruebas (vacía: pytest no se ha visto en el curso)
│
└── app/                   el paquete Python de la aplicación
    ├── main.py            crea la app y monta los routers
    ├── core/              infraestructura: config, conexión, seguridad
    ├── models/            las tablas (SQLAlchemy)
    ├── schemas/           qué recibe y qué devuelve la API (Pydantic)
    ├── services/          las reglas de negocio (RN)
    └── api/
        ├── dependencies.py   sesión de BD y usuario autenticado
        └── v1/               los endpoints
```

### Qué va en cada carpeta

| Carpeta | Qué va | Qué NO va |
|---|---|---|
| `core/` | Leer el `.env`, conectar a Postgres, hashear, firmar tokens | Reglas de negocio |
| `models/` | Las tablas y sus restricciones | Lógica, validaciones de entrada |
| `schemas/` | La forma del JSON de entrada y de salida | Acceso a la base |
| `services/` | Las reglas de negocio (RN-01 a RN-71) | Nada de FastAPI |
| `api/v1/` | Recibir la petición, llamar al servicio, responder | Decisiones de negocio |
| `scripts/` | Seeds y tareas manuales | Nada que la API necesite en tiempo de ejecución |

**La regla:** `api/` recibe y responde, `services/` decide, `models/`
persiste. Si escribes un `if` que corresponde a una regla del documento de
negocio, va en `services/`.

Por qué existe esa separación y cómo trabajar dentro de ella está en la
guía del equipo.

---

## Convenciones

- Tablas, columnas, funciones y archivos **en español**, `snake_case`
- **Sin abreviaturas**: `database.py`, no `db.py`; `dependencies.py`, no `deps.py`
- Todas las llaves primarias son **UUID**
- Todas las fechas en **UTC**
- Los endpoints se declaran con `def`, **no** con `async def` — el acceso a
  datos es síncrono
- Cada regla de negocio implementada lleva su comentario `# RN-XX`