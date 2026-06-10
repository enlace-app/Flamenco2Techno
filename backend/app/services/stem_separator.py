"""
Servicio de separación de stems usando Demucs.
Separa el audio en: vocals, drums, bass, other.
"""

import shutil
import subprocess
from pathlib import Path

import structlog

from app.config import settings

log = structlog.get_logger(__name__)


class StemSeparator:
    """
    Separador de stems usando el modelo Demucs htdemucs.
    Genera 4 stems: vocals, drums, bass, other (melodía/acompañamiento).
    """

    def __init__(
        self,
        model: str = None,
        output_dir: Path = None,
    ):
        self.model = model or settings.DEMUCS_MODEL
        self.output_dir = output_dir or settings.STEMS_DIR

    def separate(self, file_path: str, job_id: str) -> dict[str, Path]:
        """
        Separa el audio en stems usando Demucs.

        Args:
            file_path: Ruta al archivo de audio original
            job_id: ID del job (para nombrar el directorio de salida)

        Returns:
            Diccionario {stem_name: path} con las 4 pistas

        Raises:
            RuntimeError: Si Demucs falla
        """
        input_path = Path(file_path)
        if not input_path.exists():
            raise RuntimeError(f"Archivo no encontrado: {file_path}")

        # Directorio de salida para este job
        job_stem_dir = self.output_dir / job_id
        job_stem_dir.mkdir(parents=True, exist_ok=True)

        log.info(
            "Starting stem separation",
            model=self.model,
            file=input_path.name,
            output=str(job_stem_dir),
        )

        # Ejecutar Demucs como subproceso
        # Demucs crea automáticamente: output_dir/model/filename/{vocals,drums,bass,other}.wav
        cmd = [
            "python", "-m", "demucs",
            "--name", self.model,
            "--out", str(job_stem_dir),
            "--two-stems", "vocals",  # Solo separar voz del resto (más rápido)
            # Para 4 stems completos, eliminar --two-stems:
            # "--", str(input_path),
            str(input_path),
        ]

        # Comando alternativo para 4 stems completos (más lento, ~2x)
        cmd_4stems = [
            "python", "-m", "demucs",
            "--name", self.model,
            "--out", str(job_stem_dir),
            str(input_path),
        ]

        try:
            result = subprocess.run(
                cmd_4stems,
                capture_output=True,
                text=True,
                timeout=settings.CELERY_TASK_TIME_LIMIT - 60,  # Dejar margen
                check=False,
            )

            if result.returncode != 0:
                log.error(
                    "Demucs failed",
                    returncode=result.returncode,
                    stderr=result.stderr[:500],
                )
                raise RuntimeError(f"Demucs error: {result.stderr[:200]}")

        except subprocess.TimeoutExpired:
            raise RuntimeError("Demucs tardó demasiado (timeout)")

        # ── Encontrar archivos generados ──────────────────────────────
        # Demucs crea: job_stem_dir/htdemucs/<nombre_sin_ext>/{vocals,drums,bass,other}.wav
        stem_base = job_stem_dir / self.model / input_path.stem
        if not stem_base.exists():
            raise RuntimeError(f"Demucs no generó archivos en {stem_base}")

        stems = {}
        for stem_name in ["vocals", "drums", "bass", "other"]:
            stem_file = stem_base / f"{stem_name}.wav"
            if stem_file.exists():
                stems[stem_name] = stem_file
                log.info("Stem found", stem=stem_name, size_mb=stem_file.stat().st_size / 1e6)
            else:
                log.warning("Stem not found", stem=stem_name, path=str(stem_file))

        if not stems:
            raise RuntimeError("Demucs no generó ningún stem")

        return stems

    def cleanup(self, job_id: str):
        """Elimina los stems temporales de un job."""
        job_stem_dir = self.output_dir / job_id
        if job_stem_dir.exists():
            shutil.rmtree(job_stem_dir, ignore_errors=True)
            log.info("Stems cleaned up", job_id=job_id)
