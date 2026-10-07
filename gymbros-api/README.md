# GymBros API

Backend de GymBros: FastAPI + PostgreSQL.

---

## Levantar el proyecto

Hay dos modos. **Docker es el recomendado** — te da Python y PostgreSQL con
la versión correcta sin instalar nada. El modo local existe para quien no
pueda usar Docker.

### Paso común: crear tu `.env`

El `.env` no está en el repositorio porque contiene secretos. Cada quien
crea el suyo a partir de la plantilla:

```powershell
Copy-Item .env.example .env
```

Genera un secreto real y pégalo en `JWT_SECRET`:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**La app no arranca si dejas el valor de ejemplo.** Es a propósito: un
secreto que está escrito en el repositorio no es un secreto. Lo mismo si
falta `DATABASE_URL` o `JWT_SECRET` — mejor un error al arrancar que un
problema silencioso.

---

### Modo A — Docker (recomendado)

Hay dos bases posibles. Elige una en el `.env` (deja activa una sola
`DATABASE_URL`).

**A1 — Base compartida (Supabase), la de todos los días.** Pon la contraseña
de Supabase en la `DATABASE_URL` que viene activa en el `.env.example` y,
desde la **raíz del monorepo**:

```powershell
docker compose up --build
```

Solo arranca la API; la base es la del equipo. El `--build` hace falta la
primera vez o cuando cambie el `Dockerfile` o el `requirements.txt`.

**A2 — Base local, para pruebas destructivas o sin conexión.** Activa la
`DATABASE_URL` con host `db` (el nombre del servicio de PostgreSQL dentro de la
red de Docker) y levanta también el contenedor de Postgres:

```powershell
docker compose --profile local up --build
```

Una base local recién creada está vacía: aplica las migraciones y el seed (ver
*Comandos útiles* y *Datos de ejemplo*).

> **No corras pruebas que creen o borren datos contra Supabase.** Todo el
> equipo trabaja sobre esa base. Para eso está A2.

---

### Modo B — Local con venv

Puedes usar la base compartida (Supabase) con la `DATABASE_URL` que viene
activa, o una local: en ese caso necesitas **PostgreSQL 16** instalado, una
base llamada `gymbros` y activar la `DATABASE_URL` de `localhost`.

```powershell
cd gymbros-api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Para arrancar:

```powershell
uvicorn app.main:app --reload
```

---

## Verificar que funciona

| Qué | URL |
|---|---|
| Comprobación de vida | http://localhost:8001/salud |
| Swagger (documentación y pruebas) | http://localhost:8001/docs |

> El puerto es **8001**, no 8000. Se cambió porque el 8000 suele estar
> ocupado por otros proyectos. En modo local con venv, uvicorn usa el
> 8000 salvo que le pases `--port 8001`.

`/docs` es el banco de pruebas del sprint: lista todos los endpoints y
permite ejecutarlos desde el navegador. No hay que configurarlo — se
genera solo a partir de las anotaciones de tipos del código.

---

## Comandos útiles

| Qué quieres | Comando |
|---|---|
| Levantar (Supabase) | `docker compose up` |
| Levantar (base local) | `docker compose --profile local up` |
| Apagar | `docker compose --profile local down` |
| Borrar la base **local** y empezar limpio | `docker compose --profile local down -v` |
| Ver los logs de la API | `docker compose logs -f api` |
| Terminal dentro del contenedor | `docker compose exec api sh` (la imagen es Alpine: no trae `bash`) |
| Consola de PostgreSQL local | `docker compose exec db psql -U gymbros -d gymbros` |
| Ver en qué migración está la base | `docker compose exec api alembic current` |
| Aplicar migraciones | `docker compose exec api alembic upgrade head` |

Los cambios en archivos `.py` se recargan solos: el código está montado
como volumen y uvicorn corre con `--reload`.

### Migraciones en la base compartida

En Supabase la base es una sola para todo el equipo, así que una migración
aplicada allí la ve todo el mundo:

- Antes de migrar, revisa en qué revisión está: `alembic current`.
- **Solo se aplican en Supabase migraciones que ya están en `dev`.** Una
  migración de una rama sin mergear deja la base adelantada respecto al código
  de los demás, y su `alembic upgrade` falla o, peor, el esquema no coincide
  con sus modelos.
- Las migraciones de una rama se prueban primero en la base local (A2).

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
falta, así que se puede repetir sin duplicar.

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