# ── Stage 1: Base con dependencias del sistema ─────────────────────────────
FROM python:3.12-slim AS base

LABEL maintainer="Flamenco2Techno AI"
LABEL description="Backend FastAPI para conversión de audio a Techno con IA"

# Variables de entorno para Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Dependencias del sistema necesarias para audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    # FFmpeg para codificación de audio
    ffmpeg \
    # libsndfile para librosa/soundfile
    libsndfile1 \
    # libmagic para validación de archivos
    libmagic1 \
    libmagic-dev \
    # Dependencias de compilación para paquetes Python con extensiones C
    build-essential \
    git \
    wget \
    curl \
    # Torch requiere estas libs
    libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

# ── Stage 2: Instalación de dependencias Python ────────────────────────────
FROM base AS deps

WORKDIR /app

# Copiar requirements primero (caché de Docker)
COPY requirements.txt .

# Instalar dependencias base
RUN pip install --upgrade pip setuptools wheel

# Instalar PyTorch (CPU para producción básica; cambiar a CUDA en GPU server)
# Para GPU: pip install torch==2.3.0 torchaudio==2.3.0 --index-url https://download.pytorch.org/whl/cu121
RUN pip install torch==2.3.0 torchaudio==2.3.0 --index-url https://download.pytorch.org/whl/cpu

# Instalar Demucs para separación de stems
RUN pip install demucs==4.0.1

# Instalar AudioCraft (MusicGen) - puede tardar varios minutos
RUN pip install audiocraft==1.3.0 || \
    echo "WARN: AudioCraft no disponible, se usará generación alternativa"

# Instalar el resto de dependencias
RUN pip install -r requirements.txt

# ── Stage 3: Aplicación final ──────────────────────────────────────────────
FROM deps AS app

WORKDIR /app

# Copiar código fuente
COPY app/ ./app/
COPY tests/ ./tests/
COPY .env.example .env

# Crear directorios de trabajo
RUN mkdir -p \
    /app/storage/uploads \
    /app/storage/stems \
    /app/storage/output \
    /app/storage/temp \
    /app/logs

# Pre-descargar modelo Demucs htdemucs (4 stems)
# Esto evita descargarlo en primera petición (el modelo pesa ~80MB)
RUN python -c "import demucs.pretrained; demucs.pretrained.get_model('htdemucs')" || \
    echo "WARN: No se pudo pre-descargar modelo Demucs"

# Exponer puerto FastAPI
EXPOSE 8000

# Script de inicio
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Usuario no-root para seguridad
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app /app/storage
USER appuser

ENTRYPOINT ["/entrypoint.sh"]
CMD ["api"]
