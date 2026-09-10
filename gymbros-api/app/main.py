"""Punto de entrada ASGI de GymBros API.

Crea la aplicación FastAPI. Por ahora solo expone `/salud`; los routers de
negocio, el middleware, los exception handlers y los eventos de arranque se
montan aquí a medida que se implementan.
"""

from fastapi import FastAPI

VERSION = "0.1.0"

app = FastAPI(
    title="GymBros API",
    version=VERSION,
)


# Los endpoints se declaran con `def`, no con `async def`: el acceso a datos es
# síncrono (SQLAlchemy sin driver async). Una función `async` que ejecuta una
# consulta bloqueante congela el event loop y degrada todas las peticiones en
# curso, sin fallar ni avisar. Con `def`, FastAPI la corre en un hilo aparte.
@app.get("/salud", tags=["salud"])
def salud() -> dict[str, str]:
    """Comprobación de vida.

    Responde algo fijo, sin tocar la base de datos ni la configuración. Es el
    primer punto donde se ve el montaje funcionando: confirma que uvicorn
    levanta, que el puerto está bien expuesto (Docker) y que Swagger (`/docs`)
    renderiza.
    """
    return {"estado": "ok", "servicio": "gymbros-api", "version": VERSION}