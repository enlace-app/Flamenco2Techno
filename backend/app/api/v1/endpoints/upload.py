"""
Endpoint POST /upload
Recibe el archivo de audio, lo valida y crea el Job en base de datos.
"""

import uuid
from pathlib import Path

import aiofiles
import structlog
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_db
from app.core.security import validate_audio_file, FileValidationError
from app.models.job import Job, JobStatus

log = structlog.get_logger(__name__)
router = APIRouter()


class UploadResponse(BaseModel):
    job_id: str
    filename: str
    file_size_bytes: int
    message: str


@router.post(
    "/",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Subir archivo de audio",
    description="Sube un archivo MP3, WAV o FLAC para su conversión a Techno.",
)
async def upload_audio(
    file: UploadFile = File(..., description="Archivo de audio (MP3, WAV, FLAC)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Recibe un archivo de audio y:
    1. Valida nombre, tamaño y tipo MIME real
    2. Lo guarda en disco
    3. Crea un Job en base de datos
    4. Devuelve el job_id para los siguientes pasos
    """

    # ── 1. Validación inicial del nombre ─────────────────────────────
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Nombre de archivo requerido",
        )

    # Leer tamaño del archivo de cabeceras (si está disponible)
    content_length = file.size or 0

    # Validar tamaño antes de leer el contenido completo
    if content_length > settings.MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Archivo demasiado grande. Máximo: {settings.MAX_FILE_SIZE_MB} MB",
        )

    # ── 2. Guardar archivo en disco ───────────────────────────────────
    job_id = str(uuid.uuid4())
    upload_dir = settings.UPLOAD_DIR
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Nombre de archivo en disco: job_id + extensión original (evitar colisiones)
    ext = Path(file.filename).suffix.lower()
    disk_filename = f"{job_id}{ext}"
    file_path = upload_dir / disk_filename

    total_size = 0
    chunk_size = 1024 * 1024  # 1 MB por chunk

    try:
        async with aiofiles.open(file_path, "wb") as out_file:
            while chunk := await file.read(chunk_size):
                total_size += len(chunk)

                # Verificar tamaño durante la escritura (streaming protection)
                if total_size > settings.MAX_FILE_SIZE_BYTES:
                    # Borrar archivo parcial
                    file_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Archivo demasiado grande. Máximo: {settings.MAX_FILE_SIZE_MB} MB",
                    )

                await out_file.write(chunk)

    except HTTPException:
        raise
    except Exception as e:
        file_path.unlink(missing_ok=True)
        log.error("File write error", error=str(e), job_id=job_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar el archivo: {str(e)}",
        )

    # ── 3. Validación completa (MIME, hash) ───────────────────────────
    try:
        validation = validate_audio_file(
            file_path=file_path,
            original_filename=file.filename,
            file_size=total_size,
        )
    except FileValidationError as e:
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    # ── 4. Crear Job en base de datos ─────────────────────────────────
    job = Job(
        id=uuid.UUID(job_id),
        original_filename=file.filename,
        safe_filename=validation["safe_filename"],
        file_path=str(file_path),
        file_size_bytes=total_size,
        file_hash=validation["file_hash"],
        mime_type=validation["mime_type"],
        status=JobStatus.PENDING,
    )

    db.add(job)
    await db.flush()

    log.info(
        "File uploaded",
        job_id=job_id,
        filename=file.filename,
        size_mb=round(total_size / 1024 / 1024, 2),
        mime=validation["mime_type"],
    )

    return UploadResponse(
        job_id=job_id,
        filename=validation["safe_filename"],
        file_size_bytes=total_size,
        message="Archivo subido correctamente. Procede al análisis.",
    )
