"""
Modelo ORM del Job de procesamiento.
Representa el estado completo de un trabajo de conversión.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    Boolean,
    Enum,
)
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class JobStatus(str, PyEnum):
    """Estados posibles de un job."""
    PENDING = "pending"
    UPLOADING = "uploading"
    ANALYZING = "analyzing"
    SEPARATING = "separating"
    GENERATING = "generating"
    MIXING = "mixing"
    EXPORTING = "exporting"
    COMPLETED = "completed"
    FAILED = "failed"


class TechnoMode(str, PyEnum):
    """Modos de conversión disponibles."""
    SOFT = "soft"
    PEAK = "peak"
    HARD = "hard"


class Job(Base):
    """
    Tabla principal de jobs de procesamiento.
    Cada vez que un usuario sube un archivo se crea un Job.
    """
    __tablename__ = "jobs"

    # ── Identificadores ───────────────────────────────────────────────
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    conversion_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="ID único de la tarea de conversión (distinto del upload_id)",
    )

    # ── Archivo de entrada ────────────────────────────────────────────
    original_filename = Column(String(255), nullable=False)
    safe_filename = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=True)         # Ruta en disco
    file_size_bytes = Column(Integer, nullable=True)
    file_hash = Column(String(64), nullable=True)   # SHA-256
    mime_type = Column(String(50), nullable=True)

    # ── Análisis musical ──────────────────────────────────────────────
    bpm = Column(Float, nullable=True)
    musical_key = Column(String(10), nullable=True)
    musical_scale = Column(String(20), nullable=True)
    duration_seconds = Column(Float, nullable=True)
    vocals_detected = Column(Boolean, nullable=True)
    drums_detected = Column(Boolean, nullable=True)
    bass_detected = Column(Boolean, nullable=True)
    structure_sections = Column(Text, nullable=True)  # JSON array serializado

    # ── Parámetros de conversión ──────────────────────────────────────
    mode = Column(Enum(TechnoMode), nullable=True)
    keep_vocals = Column(Boolean, default=True)
    target_bpm = Column(Integer, nullable=True)
    export_format = Column(String(10), default="mp3")

    # ── Estado del procesamiento ──────────────────────────────────────
    status = Column(
        Enum(JobStatus),
        default=JobStatus.PENDING,
        nullable=False,
        index=True,
    )
    progress = Column(Float, default=0.0)           # 0.0 a 1.0
    current_step = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)

    # ── Archivo de salida ─────────────────────────────────────────────
    output_path = Column(Text, nullable=True)       # Ruta al archivo convertido
    output_size_bytes = Column(Integer, nullable=True)

    # ── Celery ───────────────────────────────────────────────────────
    celery_task_id = Column(String(255), nullable=True)

    # ── Timestamps ───────────────────────────────────────────────────
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<Job id={str(self.id)[:8]} status={self.status} bpm={self.bpm}>"

    @property
    def id_str(self) -> str:
        return str(self.id)

    @property
    def conversion_id_str(self) -> str:
        return str(self.conversion_id) if self.conversion_id else ""
