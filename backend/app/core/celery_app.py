"""
Configuración de Celery para procesamiento asíncrono de audio.
"""

from celery import Celery
from app.config import settings

# Crear instancia de Celery
celery_app = Celery(
    "flamenco2techno",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    # ── Serialización ─────────────────────────────────────────────────
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # ── Timeouts ──────────────────────────────────────────────────────
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,

    # ── Reintentos ────────────────────────────────────────────────────
    task_max_retries=settings.CELERY_MAX_RETRIES,
    task_acks_late=True,         # Confirmar tarea solo cuando termina
    task_reject_on_worker_lost=True,

    # ── Concurrencia ──────────────────────────────────────────────────
    worker_prefetch_multiplier=1,  # Un job por worker (pesados en CPU/RAM)
    worker_max_tasks_per_child=10, # Reiniciar worker tras 10 tareas (liberar RAM)

    # ── Caché de resultados ───────────────────────────────────────────
    result_expires=86400,  # Resultados en Redis por 24h

    # ── Routing de tareas ─────────────────────────────────────────────
    task_routes={
        "app.workers.conversion_worker.run_conversion": {"queue": "conversion"},
        "app.workers.conversion_worker.run_analysis": {"queue": "analysis"},
    },

    # ── Logging ───────────────────────────────────────────────────────
    worker_hijack_root_logger=False,
)

# Autodescubrimiento de tareas en el módulo workers
celery_app.autodiscover_tasks(["app.workers"])
