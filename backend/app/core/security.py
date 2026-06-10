"""
Seguridad: validación de archivos de audio subidos por el usuario.
Protege contra archivos maliciosos, spoofing de extensión y archivos oversized.
"""

import hashlib
import re
from pathlib import Path
from typing import BinaryIO

import magic  # python-magic para detección MIME real
import structlog

from app.config import settings

log = structlog.get_logger(__name__)

# MIME types de audio permitidos según la firma real del archivo
ALLOWED_MIME_TYPES = {
    "audio/mpeg",        # MP3
    "audio/mp3",
    "audio/x-mpeg",
    "audio/wav",         # WAV
    "audio/x-wav",
    "audio/vnd.wave",
    "audio/flac",        # FLAC
    "audio/x-flac",
}

# Extensiones permitidas (nombre del archivo)
ALLOWED_EXTENSIONS = {".mp3", ".wav", ".flac"}

# Tamaño máximo de nombre de archivo (evitar path traversal con nombres largos)
MAX_FILENAME_LENGTH = 255

# Regex para nombres de archivo seguros
SAFE_FILENAME_PATTERN = re.compile(r"^[\w\-. ]+$")


class FileValidationError(ValueError):
    """Error de validación de archivo."""
    pass


def validate_filename(filename: str) -> str:
    """
    Valida y sanitiza el nombre de archivo.

    Args:
        filename: Nombre original del archivo

    Returns:
        Nombre de archivo sanitizado

    Raises:
        FileValidationError: Si el nombre es inválido o peligroso
    """
    if not filename:
        raise FileValidationError("Nombre de archivo vacío")

    # Eliminar path components (prevenir directory traversal)
    safe_name = Path(filename).name

    if len(safe_name) > MAX_FILENAME_LENGTH:
        raise FileValidationError(
            f"Nombre de archivo demasiado largo (máx. {MAX_FILENAME_LENGTH} caracteres)"
        )

    # Verificar extensión
    ext = Path(safe_name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise FileValidationError(
            f"Extensión '{ext}' no permitida. Usa: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Sanitizar caracteres peligrosos (pero permitir caracteres normales de nombre)
    # Reemplazar caracteres problemáticos con guión bajo
    sanitized = re.sub(r'[^\w\-. ]', '_', safe_name)

    return sanitized


def validate_file_size(file_size: int) -> None:
    """
    Verifica que el archivo no supere el tamaño máximo permitido.

    Args:
        file_size: Tamaño en bytes

    Raises:
        FileValidationError: Si el archivo es demasiado grande
    """
    if file_size <= 0:
        raise FileValidationError("El archivo está vacío")

    if file_size > settings.MAX_FILE_SIZE_BYTES:
        max_mb = settings.MAX_FILE_SIZE_MB
        actual_mb = file_size / (1024 * 1024)
        raise FileValidationError(
            f"Archivo demasiado grande ({actual_mb:.1f} MB). Máximo: {max_mb} MB"
        )


def validate_mime_type(file_path: Path) -> str:
    """
    Verifica el tipo MIME real del archivo usando libmagic.
    Detecta archivos renombrados maliciosamente (ej: ejecutable.mp3).

    Args:
        file_path: Ruta al archivo guardado en disco

    Returns:
        Tipo MIME detectado

    Raises:
        FileValidationError: Si el tipo MIME no es un audio permitido
    """
    try:
        detected_mime = magic.from_file(str(file_path), mime=True)
    except Exception as e:
        log.warning("MIME detection failed", path=str(file_path), error=str(e))
        # Si libmagic falla, intentar por extensión como fallback
        ext = file_path.suffix.lower()
        mime_fallback = {
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".flac": "audio/flac",
        }
        detected_mime = mime_fallback.get(ext, "unknown")

    if detected_mime not in ALLOWED_MIME_TYPES:
        raise FileValidationError(
            f"El archivo no es audio válido (detectado: {detected_mime}). "
            f"Usa MP3, WAV o FLAC."
        )

    log.debug("MIME validated", mime=detected_mime, path=str(file_path))
    return detected_mime


def compute_file_hash(file_path: Path) -> str:
    """
    Calcula el hash SHA-256 del archivo.
    Útil para detectar duplicados y como identificador único.

    Args:
        file_path: Ruta al archivo

    Returns:
        Hash SHA-256 en formato hex
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def validate_audio_file(file_path: Path, original_filename: str, file_size: int) -> dict:
    """
    Validación completa de un archivo de audio.

    Args:
        file_path: Ruta donde se guardó el archivo
        original_filename: Nombre original del upload
        file_size: Tamaño en bytes

    Returns:
        Dict con metadatos de validación

    Raises:
        FileValidationError: Si alguna validación falla
    """
    # 1. Validar nombre
    safe_name = validate_filename(original_filename)

    # 2. Validar tamaño
    validate_file_size(file_size)

    # 3. Validar MIME real (anti-spoofing)
    mime_type = validate_mime_type(file_path)

    # 4. Hash para deduplicación
    file_hash = compute_file_hash(file_path)

    log.info(
        "File validated",
        filename=safe_name,
        size_mb=round(file_size / 1024 / 1024, 2),
        mime=mime_type,
        hash=file_hash[:16] + "...",
    )

    return {
        "safe_filename": safe_name,
        "mime_type": mime_type,
        "file_hash": file_hash,
        "file_size_bytes": file_size,
    }
