"""
Flamenco2Techno AI - Backend FastAPI
Punto de entrada principal de la aplicación.
"""

import time
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.api.v1.router import api_router
from app.core.database import init_db
from app.core.logging import setup_logging

# Configurar logging estructurado al arrancar
setup_logging()
log = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida de la aplicación: startup y shutdown."""
    # ── Startup ──────────────────────────────────────────────────────
    log.info("Starting Flamenco2Techno API", version=settings.APP_VERSION)

    # Inicializar base de datos (crear tablas si no existen)
    await init_db()
    log.info("Database initialized")

    # Verificar que FFmpeg está disponible
    import shutil
    if not shutil.which("ffmpeg"):
        log.warning("FFmpeg not found in PATH - audio export will fail")
    else:
        log.info("FFmpeg available")

    yield

    # ── Shutdown ─────────────────────────────────────────────────────
    log.info("Shutting down Flamenco2Techno API")


# ── Instancia FastAPI ─────────────────────────────────────────────────────
app = FastAPI(
    title="Flamenco2Techno AI API",
    description="API para conversión de audio a estilo Techno usando IA",
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,   # Swagger solo en dev
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# ── Middlewares ───────────────────────────────────────────────────────────

# CORS: permitir peticiones desde la app Flutter (en desarrollo cualquier origen)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Compresión gzip para respuestas grandes
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware de logging de cada petición HTTP."""
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = (time.perf_counter() - start) * 1000

    log.info(
        "http_request",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=round(elapsed, 2),
    )
    return response


# ── Manejadores de errores globales ───────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Captura errores no manejados y devuelve JSON limpio."""
    log.error("Unhandled exception", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor", "type": type(exc).__name__},
    )


# ── Rutas ─────────────────────────────────────────────────────────────────

# Health check (sin autenticación, para Docker healthcheck)
@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}


# Registrar router principal v1
app.include_router(api_router, prefix="/api/v1")
