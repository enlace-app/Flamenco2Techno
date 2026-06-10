"""
Fixtures compartidas para todos los tests.
"""

import asyncio
import pytest
import numpy as np
import soundfile as sf
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_wav(tmp_path) -> Path:
    sr = 22050
    duration = 10
    t = np.linspace(0, duration, sr * duration)
    audio = 0.5 * np.sin(2 * np.pi * 440 * t)
    path = tmp_path / "sample.wav"
    sf.write(str(path), audio, sr)
    return path


@pytest.fixture
def mock_db_session():
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def mock_job():
    job = MagicMock()
    job.id_str = "test-job-id-1234"
    job.bpm = 95.0
    job.musical_key = "A"
    job.musical_scale = "minor"
    job.duration_seconds = 210.5
    job.vocals_detected = True
    job.drums_detected = True
    job.bass_detected = True
    job.structure_sections = '["intro","verse","chorus","outro"]'
    job.file_path = "/tmp/test_audio.wav"
    job.safe_filename = "test_audio.wav"
    job.status.value = "completed"
    job.progress = 1.0
    job.current_step = "Completado"
    job.output_path = "/tmp/output_techno.mp3"
    return job
