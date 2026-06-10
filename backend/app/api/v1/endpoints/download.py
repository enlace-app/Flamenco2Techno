"""
Endpoint GET /download/{job_id}
Sirve el archivo de audio convertido.
"""

import uuid
from pathlib import Path

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.job import Job

log = structlog.get_logger(__name__)
router = APIRouter()


@router.get(
    "/{job_id}",
    summary="Descargar audio convertido",
    description="Descarga el archivo de audio convertido cuando status == completed.",
    response_class=FileResponse,
)
async def download_result(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Sirve el archivo de audio convertido con las cabeceras correctas
    para que el cliente Android pueda descargarlo directamente.
    """

    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="job_id no es un UUID válido",
        )

    # Buscar por conversion_id o job id
    result = await db.execute(
        select(Job).where(Job.conversion_id == job_uuid)
    )
    job: Job | None = result.scalar_one_or_none()

    if not job:
        result = await db.execute(select(Job).where(Job.id == job_uuid))
        job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job no encontrado",
        )

    if job.status.value != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El job aún no está completado (estado actual: {job.status.value})",
        )

    if not job.output_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archivo de salida no disponible",
        )

    output_path = Path(job.output_path)
    if not output_path.exists():
        log.error("Output file missing from disk", job_id=job_id, path=str(output_path))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El archivo de salida no existe en disco (puede haber expirado)",
        )

    # Determinar tipo MIME y nombre de descarga
    ext = output_path.suffix.lower()
    media_type_map = {
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".flac": "audio/flac",
    }
    media_type = media_type_map.get(ext, "application/octet-stream")

    # Nombre del archivo descargado: techno_<nombre_original>
    original_base = Path(job.safe_filename).stem
    download_name = f"techno_{original_base}{ext}"

    log.info(
        "File download started",
        job_id=job_id,
        filename=download_name,
        size_bytes=job.output_size_bytes,
    )

    return FileResponse(
        path=str(output_path),
        media_type=media_type,
        filename=download_name,
        headers={
            "Content-Disposition": f'attachment; filename="{download_name}"',
            "X-Job-Id": job_id,
        },
    )
