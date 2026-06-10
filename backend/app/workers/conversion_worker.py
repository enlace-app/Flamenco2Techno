"""
Worker Celery principal: orquesta todo el pipeline de conversión.

Pipeline:
  1. Separación de stems (Demucs)
  2. Ajuste de tempo (librosa time-stretch)
  3. Generación de elementos Techno (TechnoGenerator)
  4. Mezcla y efectos (AudioExporter + Pedalboard)
  5. Exportación final (FFmpeg)
  6. Actualización de estado en DB
"""

import asyncio
import uuid
from datetime import datetime, timezone
from pathlib import Path

import structlog
from celery import Task
from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy import select

from app.core.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.config import settings
from app.models.job import Job, JobStatus
from app.services.stem_separator import StemSeparator
from app.services.techno_generator import TechnoGenerator
from app.services.audio_exporter import AudioExporter

log = structlog.get_logger(__name__)


# ── Helper: actualizar estado del job en DB ──────────────────────────────

def update_job_status(
    job_id: str,
    conversion_id: str,
    status: JobStatus,
    progress: float,
    current_step: str,
    error_message: str = None,
    output_path: str = None,
    output_size: int = None,
):
    """
    Actualiza el estado del job en la base de datos (síncrono via asyncio.run).
    """
    async def _update():
        async with AsyncSessionLocal() as db:
            # Buscar por conversion_id
            result = await db.execute(
                select(Job).where(Job.conversion_id == uuid.UUID(conversion_id))
            )
            job = result.scalar_one_or_none()

            if job:
                job.status = status
                job.progress = progress
                job.current_step = current_step
                if error_message is not None:
                    job.error_message = error_message
                if output_path is not None:
                    job.output_path = output_path
                if output_size is not None:
                    job.output_size_bytes = output_size
                if status == JobStatus.COMPLETED:
                    job.completed_at = datetime.now(timezone.utc)
                await db.commit()

    try:
        asyncio.run(_update())
    except Exception as e:
        log.error("Failed to update job status", error=str(e), job_id=job_id)


# ── Tarea Celery principal ────────────────────────────────────────────────

@celery_app.task(
    name="app.workers.conversion_worker.run_conversion",
    bind=True,
    max_retries=settings.CELERY_MAX_RETRIES,
    default_retry_delay=30,
    soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
    time_limit=settings.CELERY_TASK_TIME_LIMIT,
    acks_late=True,
    reject_on_worker_lost=True,
)
def run_conversion(
    self: Task,
    job_id: str,
    conversion_id: str,
    mode: str = "peak",
    keep_vocals: bool = True,
    target_bpm: int = 130,
    export_format: str = "mp3",
    original_bpm: float = 120.0,
    musical_key: str = "C",
    file_path: str = None,
) -> dict:
    """
    Tarea Celery principal de conversión a Techno.
    Orquesta todo el pipeline desde la separación hasta la exportación.
    """
    log.info(
        "Conversion task started",
        job_id=job_id,
        conversion_id=conversion_id,
        mode=mode,
        target_bpm=target_bpm,
        keep_vocals=keep_vocals,
    )

    # Directorio de trabajo para este job
    work_dir = settings.TEMP_DIR / conversion_id
    work_dir.mkdir(parents=True, exist_ok=True)

    try:
        # ── PASO 1: Separación de stems (Demucs) ──────────────────────
        _update(conversion_id, job_id, JobStatus.SEPARATING, 0.05,
                "Separando voz e instrumentos con Demucs...")

        separator = StemSeparator()
        stems = separator.separate(file_path, conversion_id)

        vocals_path = stems.get("vocals")
        drums_original = stems.get("drums")
        bass_original = stems.get("bass")
        other_path = stems.get("other")

        log.info("Stems separated", stems=list(stems.keys()))
        _update(conversion_id, job_id, JobStatus.SEPARATING, 0.25,
                "Stems separados. Ajustando tempo...")

        # ── PASO 2: Ajuste de tempo ────────────────────────────────────
        _update(conversion_id, job_id, JobStatus.GENERATING, 0.30,
                f"Ajustando tempo a {target_bpm} BPM...")

        import soundfile as sf
        import numpy as np
        exporter_svc = AudioExporter()

        if vocals_path and vocals_path.exists() and keep_vocals:
            y_vocals, sr = sf.read(str(vocals_path), always_2d=False)
            if len(y_vocals.shape) > 1:
                y_vocals = np.mean(y_vocals, axis=1)
            y_vocals_stretched = exporter_svc.adjust_tempo(y_vocals, original_bpm, target_bpm)
            stretched_vocals_path = work_dir / "vocals_stretched.wav"
            sf.write(str(stretched_vocals_path), y_vocals_stretched, sr)
            vocals_path = stretched_vocals_path

        if other_path and other_path.exists():
            y_other, sr = sf.read(str(other_path), always_2d=False)
            if len(y_other.shape) > 1:
                y_other = np.mean(y_other, axis=1)
            y_other_stretched = exporter_svc.adjust_tempo(y_other, original_bpm, target_bpm)
            stretched_other_path = work_dir / "other_stretched.wav"
            sf.write(str(stretched_other_path), y_other_stretched, sr)
            other_path = stretched_other_path

        # ── PASO 3: Generar duración ajustada ─────────────────────────
        # Calcular nueva duración tras el time-stretch
        if other_path and other_path.exists():
            y_check, sr_check = sf.read(str(other_path), always_2d=False)
            new_duration = len(y_check) / sr_check
        else:
            new_duration = len(y_vocals_stretched) / sr if vocals_path else 180.0

        # ── PASO 4: Generar elementos Techno ──────────────────────────
        _update(conversion_id, job_id, JobStatus.GENERATING, 0.45,
                f"Generando batería Techno ({mode})...")

        generator = TechnoGenerator()
        techno_elements = generator.generate_all(
            output_dir=work_dir / "techno",
            bpm=float(target_bpm),
            musical_key=musical_key,
            mode=mode,
            duration_seconds=new_duration,
        )

        log.info("Techno elements generated", elements=list(techno_elements.keys()))

        # ── PASO 5: Mezcla y efectos ───────────────────────────────────
        _update(conversion_id, job_id, JobStatus.MIXING, 0.65,
                "Mezclando y aplicando efectos Techno...")

        output_base = settings.OUTPUT_DIR / conversion_id
        output_base.parent.mkdir(parents=True, exist_ok=True)

        final_path = exporter_svc.mix_and_export(
            vocals_path=vocals_path if keep_vocals else None,
            original_other_path=other_path,
            techno_drums_path=techno_elements.get("drums"),
            techno_bass_path=techno_elements.get("bass"),
            techno_synth_path=techno_elements.get("synth"),
            output_path=output_base,
            mode=mode,
            keep_vocals=keep_vocals,
            duration_seconds=new_duration,
            export_format=export_format,
        )

        _update(conversion_id, job_id, JobStatus.EXPORTING, 0.90,
                "Exportando archivo final...")

        # ── PASO 6: Verificar archivo de salida ───────────────────────
        if not final_path.exists():
            raise RuntimeError("El archivo de salida no fue generado")

        output_size = final_path.stat().st_size
        log.info(
            "Conversion completed",
            job_id=job_id,
            output=str(final_path),
            size_mb=round(output_size / 1e6, 2),
        )

        # ── PASO 7: Marcar como completado ────────────────────────────
        update_job_status(
            job_id=job_id,
            conversion_id=conversion_id,
            status=JobStatus.COMPLETED,
            progress=1.0,
            current_step="¡Conversión completada!",
            output_path=str(final_path),
            output_size=output_size,
        )

        # Limpiar archivos temporales (stems)
        separator.cleanup(conversion_id)

        return {
            "status": "completed",
            "output_path": str(final_path),
            "output_size_bytes": output_size,
        }

    except SoftTimeLimitExceeded:
        log.error("Task soft time limit exceeded", job_id=job_id)
        update_job_status(
            job_id=job_id,
            conversion_id=conversion_id,
            status=JobStatus.FAILED,
            progress=0.0,
            current_step="Error: tiempo de procesamiento agotado",
            error_message="El proceso tardó demasiado. Intenta con un archivo más corto.",
        )
        raise

    except Exception as exc:
        log.error("Conversion task failed", job_id=job_id, error=str(exc), exc_info=True)

        # Reintentar automáticamente si quedan intentos
        if self.request.retries < self.max_retries:
            log.info("Retrying task", retry=self.request.retries + 1)
            raise self.retry(exc=exc, countdown=30)

        # Sin más reintentos: marcar como fallido
        update_job_status(
            job_id=job_id,
            conversion_id=conversion_id,
            status=JobStatus.FAILED,
            progress=0.0,
            current_step=f"Error: {str(exc)[:100]}",
            error_message=str(exc),
        )

        return {"status": "failed", "error": str(exc)}

    finally:
        # Limpiar directorio de trabajo temporal (siempre)
        import shutil
        if work_dir.exists():
            shutil.rmtree(work_dir, ignore_errors=True)


def _update(conversion_id: str, job_id: str, status: JobStatus, progress: float, step: str):
    """Helper rápido para actualizar estado."""
    update_job_status(
        job_id=job_id,
        conversion_id=conversion_id,
        status=status,
        progress=progress,
        current_step=step,
    )


# ── Tarea de análisis (opcional: delegado a Celery) ───────────────────────

@celery_app.task(
    name="app.workers.conversion_worker.run_analysis",
    bind=True,
    max_retries=1,
    soft_time_limit=120,
    time_limit=180,
)
def run_analysis(self: Task, job_id: str, file_path: str) -> dict:
    """
    Tarea Celery para análisis de audio (cuando se quiere asíncrono).
    Por defecto el análisis se hace síncrono en el endpoint.
    """
    from app.services.audio_analyzer import AudioAnalyzer
    analyzer = AudioAnalyzer()
    return analyzer.analyze(file_path)
