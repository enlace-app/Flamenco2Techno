"""
Tests del motor de generación de elementos Techno.
"""

import numpy as np
import pytest
import soundfile as sf

from app.services.techno_generator import TechnoGenerator, NOTE_FREQUENCIES


SR = 22050  # Sample rate bajo para tests rápidos
DURATION = 4.0  # 4 segundos para tests


class TestTechnoGenerator:

    @pytest.fixture
    def gen(self):
        return TechnoGenerator(sample_rate=SR)

    # ── Kick ──────────────────────────────────────────────────────────

    def test_kick_length(self, gen):
        n = int(SR * DURATION)
        kick = gen.generate_kick(bpm=130, n_samples=n, mode="peak")
        assert len(kick) == n

    def test_kick_normalized(self, gen):
        n = int(SR * DURATION)
        kick = gen.generate_kick(bpm=130, n_samples=n, mode="hard")
        assert np.max(np.abs(kick)) <= 1.0 + 1e-6

    @pytest.mark.parametrize("mode", ["soft", "peak", "hard"])
    def test_kick_all_modes(self, gen, mode):
        n = int(SR * 2)
        kick = gen.generate_kick(bpm=130, n_samples=n, mode=mode)
        assert len(kick) == n
        assert not np.all(kick == 0)

    # ── Hi-hat ────────────────────────────────────────────────────────

    def test_hihat_length(self, gen):
        n = int(SR * DURATION)
        hat = gen.generate_hihat(bpm=130, n_samples=n, mode="peak")
        assert len(hat) == n

    def test_hihat_not_silent(self, gen):
        n = int(SR * DURATION)
        hat = gen.generate_hihat(bpm=130, n_samples=n, mode="hard")
        assert np.max(np.abs(hat)) > 0.01

    # ── Snare ─────────────────────────────────────────────────────────

    def test_snare_length(self, gen):
        n = int(SR * DURATION)
        snare = gen.generate_snare(bpm=130, n_samples=n, mode="peak")
        assert len(snare) == n

    # ── Bajo ──────────────────────────────────────────────────────────

    def test_bass_length(self, gen):
        n = int(SR * DURATION)
        bass = gen.generate_bass(bpm=130, musical_key="A", n_samples=n, mode="peak")
        assert len(bass) == n

    def test_bass_normalized(self, gen):
        n = int(SR * DURATION)
        bass = gen.generate_bass(bpm=130, musical_key="C", n_samples=n, mode="soft")
        assert np.max(np.abs(bass)) <= 1.0 + 1e-6

    @pytest.mark.parametrize("key", ["C", "A", "F#", "G"])
    def test_bass_all_keys(self, gen, key):
        n = int(SR * 2)
        bass = gen.generate_bass(bpm=130, musical_key=key, n_samples=n, mode="peak")
        assert len(bass) == n

    # ── Sintetizador ──────────────────────────────────────────────────

    def test_synth_length(self, gen):
        n = int(SR * DURATION)
        synth = gen.generate_synth_pad(bpm=130, musical_key="A", n_samples=n, mode="soft")
        assert len(synth) == n

    def test_synth_amplitude_controlled(self, gen):
        n = int(SR * DURATION)
        synth = gen.generate_synth_pad(bpm=130, musical_key="C", n_samples=n, mode="peak")
        assert np.max(np.abs(synth)) <= 0.5  # Pads deben ser suaves

    # ── generate_all ──────────────────────────────────────────────────

    def test_generate_all_creates_files(self, gen, tmp_path):
        results = gen.generate_all(
            output_dir=tmp_path,
            bpm=130,
            musical_key="A",
            mode="soft",
            duration_seconds=DURATION,
        )
        for name in ["drums", "bass", "synth", "riser"]:
            assert name in results
            assert results[name].exists()

    def test_generate_all_files_readable(self, gen, tmp_path):
        results = gen.generate_all(
            output_dir=tmp_path,
            bpm=130,
            musical_key="C",
            mode="peak",
            duration_seconds=DURATION,
        )
        for name, path in results.items():
            audio, sr = sf.read(str(path))
            assert len(audio) > 0, f"Archivo {name} vacío"

    @pytest.mark.parametrize("mode", ["soft", "peak", "hard"])
    def test_generate_all_modes(self, gen, tmp_path, mode):
        results = gen.generate_all(
            output_dir=tmp_path / mode,
            bpm=130,
            musical_key="A",
            mode=mode,
            duration_seconds=3.0,
        )
        assert len(results) >= 3

    # ── Notas ─────────────────────────────────────────────────────────

    def test_note_frequencies_coverage(self):
        assert len(NOTE_FREQUENCIES) == 12
        assert "C" in NOTE_FREQUENCIES
        assert "A" in NOTE_FREQUENCIES
        assert NOTE_FREQUENCIES["A"] == pytest.approx(440.0, rel=0.01)
