"""Router raíz de la API v1: agrupa los routers de cada dominio bajo /api/v1."""

from fastapi import APIRouter

from app.api.v1 import auth, ejercicios, mediciones, usuarios

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(usuarios.router)
api_router.include_router(mediciones.router)
api_router.include_router(ejercicios.router)
