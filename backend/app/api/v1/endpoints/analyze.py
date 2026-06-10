"""
Endpoint POST /analyze
Dispara el análisis musical del archivo subido y devuelve los resultados.
"""

import json
import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.job import Job, JobStatus
from app.services.audio_analyzer import AudioAnalyzer

log = structlog.get_logger(__name__)
router = APIRouter()


class AnalyzeRequest(BaseModel):
    job_id: str


class AnalyzeResponse(BaseModel):
    job_id: str
    bpm: float
    key: str
    scale: str
    duration_seconds: float
    vocals_detected: bool
    drums_detected: bool
    bass_detected: bool
    structure_sections: list[str]


@router.post(
    "/",
    response_model=AnalyzeResponse,
    summary="Analizar archivo de audio",
    description="Analiza BPM, tonalidad, duración y stems del archivo subido.",
)
async def analyze_audio(
    body: AnalyzeRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Ejecuta el análisis musical completo:
    - BPM con Librosa beat tracking
    - Tonalidad con Librosa chroma features
    - Detección de stems (voz, batería, bajo) con análisis espectral
    - Estructura de la canción (intro, verse, chorus, etc.)
    """

    # ── Obtener Job ───────────────────────────────────────────────────
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

    if not job.file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay archivo asociado a este job",
        )

    # ── Análisis (si ya se hizo, devolver cacheado) ───────────────────
    if job.bpm is not None:
        log.info("Returning cached analysis", job_id=body.job_id)
        return _build_response(job)

    # ── Actualizar estado ─────────────────────────────────────────────
    job.status = JobStatus.ANALYZING
    job.current_step = "Analizando audio..."
    await db.flush()

    # ── Ejecutar análisis ─────────────────────────────────────────────
    try:
        analyzer = AudioAnalyzer()
        analysis = analyzer.analyze(job.file_path)
    except Exception as e:
        job.status = JobStatus.FAILED
        job.error_message = f"Error en análisis: {str(e)}"
        await db.flush()
        log.error("Analysis failed", job_id=body.job_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al analizar el archivo: {str(e)}",
        )

    # ── Guardar resultados en DB ──────────────────────────────────────
    job.bpm = analysis["bpm"]
    job.musical_key = analysis["key"]
    job.musical_scale = analysis["scale"]
    job.duration_seconds = analysis["duration_seconds"]
    job.vocals_detected = analysis["vocals_detected"]
    job.drums_detected = analysis["drums_detected"]
    job.bass_detected = analysis["bass_detected"]
    job.structure_sections = json.dumps(analysis["structure_sections"])
    job.status = JobStatus.PENDING  # Listo para conversión
    job.current_step = "Análisis completado"

    await db.flush()

    log.info(
        "Analysis completed",
        job_id=body.job_id,
        bpm=analysis["bpm"],
        key=f"{analysis['key']} {analysis['scale']}",
        duration=analysis["duration_seconds"],
    )

    return _build_response(job)


def _build_response(job: Job) -> AnalyzeResponse:
    """Construye la respuesta desde el modelo Job."""
    sections = []
    if job.structure_sections:
        try:
            sections = json.loads(job.structure_sections)
        except (json.JSONDecodeError, TypeError):
            sections = []

    return AnalyzeResponse(
        job_id=job.id_str,
        bpm=job.bpm or 0.0,
        key=job.musical_key or "C",
        scale=job.musical_scale or "major",
        duration_seconds=job.duration_seconds or 0.0,
        vocals_detected=job.vocals_detected or False,
        drums_detected=job.drums_detected or False,
        bass_detected=job.bass_detected or False,
        structure_sections=sections,
    )
