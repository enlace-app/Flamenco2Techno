"""
Tests del servicio de análisis musical.
"""

import numpy as np
import pytest
import soundfile as sf
from pathlib import Path

from app.services.audio_analyzer import AudioAnalyzer, CHROMATIC_NOTES


class TestAudioAnalyzer:

    def test_analyze_returns_all_fields(self, sample_wav):
        """El análisis debe retornar todos los campos esperados."""
        analyzer = AudioAnalyzer(sample_rate=22050)
        result = analyzer.analyze(str(sample_wav))

        required = [
            "bpm", "key", "scale", "duration_seconds",
            "vocals_detected", "drums_detected",
            "bass_detected", "structure_sections",
        ]
        for field in required:
            assert field in result, f"Campo faltante: {field}"

    def test_bpm_in_valid_range(self, sample_wav):
        analyzer = AudioAnalyzer(sample_rate=22050)
        result = analyzer.analyze(str(sample_wav))
        assert 40 <= result["bpm"] <= 300

    def test_key_is_valid_note(self, sample_wav):
        analyzer = AudioAnalyzer(sample_rate=22050)
        result = analyzer.analyze(str(sample_wav))
        assert result["key"] in CHROMATIC_NOTES

    def test_scale_is_valid(self, sample_wav):
        analyzer = AudioAnalyzer(sample_rate=22050)
        result = analyzer.analyze(str(sample_wav))
        assert result["scale"] in ("major", "minor")

    def test_duration_accuracy(self, tmp_path):
        sr = 22050
        duration = 20.0
        audio = np.zeros(int(sr * duration))
        path = tmp_path / "duration_test.wav"
        sf.write(str(path), audio, sr)

        analyzer = AudioAnalyzer(sample_rate=sr)
        result = analyzer.analyze(str(path))
        assert abs(result["duration_seconds"] - duration) < 1.0

    def test_structure_sections_is_list(self, sample_wav):
        analyzer = AudioAnalyzer(sample_rate=22050)
        result = analyzer.analyze(str(sample_wav))
        assert isinstance(result["structure_sections"], list)
        assert len(result["structure_sections"]) >= 1

    def test_boolean_detections_are_bool(self, sample_wav):
        analyzer = AudioAnalyzer(sample_rate=22050)
        result = analyzer.analyze(str(sample_wav))
        assert isinstance(result["vocals_detected"], bool)
        assert isinstance(result["drums_detected"], bool)
        assert isinstance(result["bass_detected"], bool)

    def test_missing_file_raises_error(self):
        analyzer = AudioAnalyzer()
        with pytest.raises(RuntimeError, match="no encontrado"):
            analyzer.analyze("/tmp/nonexistent_xyz_audio.wav")

    def test_simple_segment_short(self):
        analyzer = AudioAnalyzer()
        sections = analyzer._simple_segment(30.0)
        assert len(sections) >= 2

    def test_simple_segment_long(self):
        analyzer = AudioAnalyzer()
        sections = analyzer._simple_segment(400.0)
        assert "chorus" in sections
        assert "bridge" in sections
