"""
Endpoint GET /status/{job_id}
Devuelve el estado actual de un job de conversión.
Diseñado para polling cada 2 segundos desde la app Flutter.
"""

import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_db
from app.models.job import Job

log = structlog.get_logger(__name__)
router = APIRouter()


class StatusResponse(BaseModel):
    job_id: str
    status: str
    progress: float
    current_step: str
    error_message: str | None = None
    download_url: str | None = None


@router.get(
    "/{job_id}",
    response_model=StatusResponse,
    summary="Consultar estado de un job",
    description="Devuelve el estado actual y progreso (0.0-1.0) de un job. Llámalo cada 2s.",
)
async def get_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint de polling para el estado del job.
    Cuando status == 'completed', incluye download_url con la URL de descarga.
    Cuando status == 'failed', incluye error_message.
    """

    # Aceptar tanto el upload job_id como el conversion_id
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="job_id no es un UUID válido",
        )

    # Buscar por conversion_id primero (polling más frecuente durante conversión)
    result = await db.execute(
        select(Job).where(Job.conversion_id == job_uuid)
    )
    job: Job | None = result.scalar_one_or_none()

    # Si no encontrado por conversion_id, buscar por id de upload
    if not job:
        result = await db.execute(select(Job).where(Job.id == job_uuid))
        job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} no encontrado o expirado",
        )

    # Construir URL de descarga cuando esté listo
    download_url = None
    if job.status.value == "completed" and job.output_path:
        download_url = f"/api/v1/download/{job_id}"

    return StatusResponse(
        job_id=job_id,
        status=job.status.value,
        progress=job.progress or 0.0,
        current_step=job.current_step or "",
        error_message=job.error_message,
        download_url=download_url,
    )
