"""
Endpoint POST /convert
Inicia la tarea Celery de conversión a Techno y devuelve el conversion_id.
"""

import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_db
from app.models.job import Job, JobStatus, TechnoMode
from app.workers.conversion_worker import run_conversion

log = structlog.get_logger(__name__)
router = APIRouter()


class ConvertRequest(BaseModel):
    job_id: str = Field(..., description="ID del job con el archivo ya analizado")
    mode: str = Field(
        default="peak",
        description="Modo de conversión: soft | peak | hard",
    )
    keep_vocals: bool = Field(
        default=True,
        description="Mantener la voz original usando Demucs",
    )
    target_bpm: int = Field(
        default=130,
        ge=settings.BPM_TARGET_MIN,
        le=settings.BPM_TARGET_MAX,
        description=f"BPM objetivo ({settings.BPM_TARGET_MIN}-{settings.BPM_TARGET_MAX})",
    )
    export_format: str = Field(
        default="mp3",
        description="Formato de exportación: mp3 | wav",
    )

    @validator("mode")
    def validate_mode(cls, v):
        allowed = {"soft", "peak", "hard"}
        if v not in allowed:
            raise ValueError(f"Modo inválido. Usa: {', '.join(allowed)}")
        return v

    @validator("export_format")
    def validate_format(cls, v):
        allowed = {"mp3", "wav"}
        if v not in allowed:
            raise ValueError(f"Formato inválido. Usa: {', '.join(allowed)}")
        return v


class ConvertResponse(BaseModel):
    job_id: str
    conversion_id: str
    status: str
    message: str


@router.post(
    "/",
    response_model=ConvertResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Iniciar conversión a Techno",
    description="Encola la tarea de conversión. Usa GET /status/{conversion_id} para seguir el progreso.",
)
async def start_conversion(
    body: ConvertRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Inicia la conversión asíncrona:
    1. Valida que el job existe y tiene análisis
    2. Genera un conversion_id único
    3. Encola la tarea Celery
    4. Devuelve el conversion_id para hacer polling

    La conversión incluye:
    - Separación de stems con Demucs
    - Generación de batería techno (kick, hi-hat, snare)
    - Generación de línea de bajo techno
    - Síntesis de pads/leads en la tonalidad original
    - Mezcla y aplicación de efectos (reverb, compressor, distortion)
    - Exportación en el formato elegido
    """

    # ── Obtener y validar Job ─────────────────────────────────────────
    try:
        job_uuid = uuid.UUID(body.job_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="job_id no es un UUID válido",
        )

    result = await db.execute(select(Job).where(Job.id == job_uuid))
    job: Job | None = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {body.job_id} no encontrado",
        )

    if not job.bpm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo debe ser analizado antes de convertir. Llama POST /analyze primero.",
        )

    # No permitir conversiones paralelas del mismo job
    if job.status in (JobStatus.SEPARATING, JobStatus.GENERATING, JobStatus.MIXING, JobStatus.EXPORTING):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya hay una conversión en curso para este job",
        )

    # ── Preparar conversión ───────────────────────────────────────────
    conversion_id = str(uuid.uuid4())

    # Actualizar Job con parámetros de conversión
    job.conversion_id = uuid.UUID(conversion_id)
    job.mode = TechnoMode(body.mode)
    job.keep_vocals = body.keep_vocals
    job.target_bpm = body.target_bpm
    job.export_format = body.export_format
    job.status = JobStatus.PENDING
    job.progress = 0.0
    job.current_step = "En cola de conversión..."
    job.error_message = None
    job.output_path = None

    await db.flush()

    # ── Encolar tarea Celery ──────────────────────────────────────────
    task = run_conversion.apply_async(
        args=[body.job_id, conversion_id],
        kwargs={
            "mode": body.mode,
            "keep_vocals": body.keep_vocals,
            "target_bpm": body.target_bpm,
            "export_format": body.export_format,
            "original_bpm": job.bpm,
            "musical_key": job.musical_key or "C",
            "file_path": job.file_path,
        },
        queue="conversion",
        task_id=conversion_id,
    )

    job.celery_task_id = task.id
    await db.flush()

    log.info(
        "Conversion queued",
        job_id=body.job_id,
        conversion_id=conversion_id,
        mode=body.mode,
        target_bpm=body.target_bpm,
        keep_vocals=body.keep_vocals,
    )

    return ConvertResponse(
        job_id=body.job_id,
        conversion_id=conversion_id,
        status="queued",
        message=f"Conversión encolada. Sigue el progreso con GET /status/{conversion_id}",
    )
