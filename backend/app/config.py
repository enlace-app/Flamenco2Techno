"""
Configuración centralizada de la aplicación.
Todas las variables se leen desde el entorno o fichero .env
"""

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Aplicación ────────────────────────────────────────────────────
    APP_NAME: str = "Flamenco2Techno AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ── Base de datos ─────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://f2t_user:f2t_secret@localhost:5432/flamenco2techno"

    # ── Redis / Celery ────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Seguridad ─────────────────────────────────────────────────────
    API_KEY: str = "dev-secret-key-change-in-production"
    ALLOWED_ORIGINS: List[str] = ["*"]   # En producción, restringir a dominio propio

    # ── Almacenamiento de archivos ─────────────────────────────────────
    STORAGE_PATH: Path = Path("/app/storage")
    MAX_FILE_SIZE_MB: int = 100
    FILE_EXPIRY_HOURS: int = 24  # Los archivos se borran tras 24h

    @property
    def UPLOAD_DIR(self) -> Path:
        return self.STORAGE_PATH / "uploads"

    @property
    def STEMS_DIR(self) -> Path:
        return self.STORAGE_PATH / "stems"

    @property
    def OUTPUT_DIR(self) -> Path:
        return self.STORAGE_PATH / "output"

    @property
    def TEMP_DIR(self) -> Path:
        return self.STORAGE_PATH / "temp"

    @property
    def MAX_FILE_SIZE_BYTES(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    # ── Audio / IA ────────────────────────────────────────────────────
    DEMUCS_MODEL: str = "htdemucs"    # Modelo de separación (4 stems)
    BPM_TARGET_MIN: int = 125
    BPM_TARGET_MAX: int = 140
    DEFAULT_TARGET_BPM: int = 130
    SAMPLE_RATE: int = 44100
    EXPORT_MP3_BITRATE: str = "320k"

    # ── Celery ────────────────────────────────────────────────────────
    CELERY_TASK_SOFT_TIME_LIMIT: int = 540   # 9 minutos
    CELERY_TASK_TIME_LIMIT: int = 600        # 10 minutos (hard limit)
    CELERY_MAX_RETRIES: int = 2

    # ── Logging ───────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # "json" para producción, "pretty" para desarrollo

    def create_dirs(self):
        """Crea los directorios de almacenamiento si no existen."""
        for d in [self.UPLOAD_DIR, self.STEMS_DIR, self.OUTPUT_DIR, self.TEMP_DIR]:
            d.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Singleton de configuración (cacheado)."""
    s = Settings()
    s.create_dirs()
    return s


# Instancia global de settings
settings = get_settings()
