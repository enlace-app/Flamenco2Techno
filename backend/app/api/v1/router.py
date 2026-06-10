"""
Router principal de la API v1.
Agrega todos los endpoints de los distintos módulos.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import upload, analyze, convert, status, download

api_router = APIRouter()

# Registrar cada sub-router con su prefijo y tags para Swagger
api_router.include_router(
    upload.router,
    prefix="/upload",
    tags=["📤 Upload"],
)
api_router.include_router(
    analyze.router,
    prefix="/analyze",
    tags=["🎵 Analysis"],
)
api_router.include_router(
    convert.router,
    prefix="/convert",
    tags=["⚡ Conversion"],
)
api_router.include_router(
    status.router,
    prefix="/status",
    tags=["📊 Status"],
)
api_router.include_router(
    download.router,
    prefix="/download",
    tags=["📥 Download"],
)
