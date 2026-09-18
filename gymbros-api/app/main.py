"""Punto de entrada ASGI de GymBros API.

Crea la aplicación FastAPI. Por ahora solo expone `/salud`; los routers de
negocio, el middleware, los exception handlers y los eventos de arranque se
montan aquí a medida que se implementan.
"""

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router

VERSION = "0.1.0"

app = FastAPI(
    title="GymBros API",
    version=VERSION,
)

app.include_router(api_router)

# Campos cuyo valor no debe salir jamás en una respuesta de error ni en logs.
_CAMPOS_SENSIBLES = {"password"}


@app.exception_handler(RequestValidationError)
def _errores_de_validacion(request: Request, exc: RequestValidationError) -> JSONResponse:
    """422 sin el eco del valor inválido.

    RN-22: la respuesta por defecto de FastAPI incluye `input` con el dato que
    falló; en el registro eso filtraría la contraseña al cuerpo de la respuesta
    y a los logs de acceso. Se elimina `input` siempre y, además, `ctx` cuando
    el error apunta a un campo sensible (algunos validadores meten el valor
    dentro de `ctx`).
    """
    errores = []
    for err in exc.errors():
        limpio = {clave: valor for clave, valor in err.items() if clave != "input"}
        if _CAMPOS_SENSIBLES.intersection(err.get("loc", ())):
            limpio.pop("ctx", None)
        errores.append(limpio)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": jsonable_encoder(errores)},
    )


