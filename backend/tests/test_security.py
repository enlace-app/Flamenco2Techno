"""
Tests del módulo de seguridad: validación de archivos.
"""

import pytest
import numpy as np
import soundfile as sf
from pathlib import Path

from app.core.security import (
    validate_filename,
    validate_file_size,
    compute_file_hash,
    FileValidationError,
)
from app.config import settings


class TestValidateFilename:

    def test_valid_mp3(self):
        assert validate_filename("cancion.mp3").endswith(".mp3")

    def test_valid_wav(self):
        assert validate_filename("audio.wav").endswith(".wav")

    def test_valid_flac(self):
        assert validate_filename("lossless.flac").endswith(".flac")

    def test_path_traversal_stripped(self):
        result = validate_filename("../../etc/passwd.mp3")
        assert "/" not in result
        assert ".." not in result

    def test_windows_path_stripped(self):
        result = validate_filename("C:\\Users\\Audio\\song.mp3")
        assert "\\" not in result

    def test_invalid_extension_exe(self):
        with pytest.raises(FileValidationError):
            validate_filename("virus.exe")

    def test_invalid_extension_php(self):
        with pytest.raises(FileValidationError):
            validate_filename("shell.php")

    def test_invalid_extension_mp4(self):
        with pytest.raises(FileValidationError):
            validate_filename("video.mp4")

    def test_empty_string(self):
        with pytest.raises(FileValidationError):
            validate_filename("")

    def test_too_long_name(self):
        with pytest.raises(FileValidationError):
            validate_filename("a" * 300 + ".mp3")

    def test_spaces_allowed(self):
        result = validate_filename("mi cancion favorita.mp3")
        assert ".mp3" in result

    def test_unicode_chars_sanitized(self):
        # Caracteres especiales deben sanitizarse sin crashear
        result = validate_filename("canción de cuna.mp3")
        assert result.endswith(".mp3")


class TestValidateFileSize:

    def test_valid_1mb(self):
        validate_file_size(1 * 1024 * 1024)  # No debe lanzar

    def test_valid_50mb(self):
        validate_file_size(50 * 1024 * 1024)

    def test_valid_exact_max(self):
        validate_file_size(settings.MAX_FILE_SIZE_BYTES)

    def test_empty_rejected(self):
        with pytest.raises(FileValidationError, match="vacío"):
            validate_file_size(0)

    def test_negative_rejected(self):
        with pytest.raises(FileValidationError):
            validate_file_size(-1)

    def test_oversized_rejected(self):
        with pytest.raises(FileValidationError, match="grande"):
            validate_file_size(settings.MAX_FILE_SIZE_BYTES + 1)

    def test_101mb_rejected(self):
        with pytest.raises(FileValidationError):
            validate_file_size(101 * 1024 * 1024)


class TestComputeFileHash:

    def test_hash_is_64_chars(self, tmp_path):
        p = tmp_path / "test.wav"
        p.write_bytes(b"test audio data")
        h = compute_file_hash(p)
        assert len(h) == 64

    def test_hash_is_hex(self, tmp_path):
        p = tmp_path / "test.wav"
        p.write_bytes(b"hello world")
        h = compute_file_hash(p)
        assert all(c in "0123456789abcdef" for c in h)

    def test_same_content_same_hash(self, tmp_path):
        content = b"audio content xyz"
        p1 = tmp_path / "a.wav"
        p2 = tmp_path / "b.wav"
        p1.write_bytes(content)
        p2.write_bytes(content)
        assert compute_file_hash(p1) == compute_file_hash(p2)

    def test_different_content_different_hash(self, tmp_path):
        p1 = tmp_path / "a.wav"
        p2 = tmp_path / "b.wav"
        p1.write_bytes(b"content A")
        p2.write_bytes(b"content B")
        assert compute_file_hash(p1) != compute_file_hash(p2)

    def test_large_file_hash(self, tmp_path):
        """Hash de archivo grande (1 MB) debe funcionar."""
        p = tmp_path / "large.wav"
        p.write_bytes(b"\x00" * 1024 * 1024)
        h = compute_file_hash(p)
        assert len(h) == 64
