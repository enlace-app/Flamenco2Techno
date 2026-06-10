"""
Motor de generación de elementos Techno.
Genera batería, bajo y sintetizadores en estilo Techno
sincronizados con la tonalidad y BPM del original.

No depende de MusicGen para los elementos básicos (más rápido y controlable).
MusicGen se usa opcionalmente para texturas de sintetizador.
"""

import math
from pathlib import Path
from typing import Optional

import numpy as np
import soundfile as sf
import structlog

from app.config import settings

log = structlog.get_logger(__name__)

# ── Constantes de síntesis ────────────────────────────────────────────────

SAMPLE_RATE = settings.SAMPLE_RATE

# Frecuencias base de las 12 notas (A4 = 440 Hz)
NOTE_FREQUENCIES = {
    "C": 261.63, "C#": 277.18, "D": 293.66, "D#": 311.13,
    "E": 329.63, "F": 349.23, "F#": 369.99, "G": 392.00,
    "G#": 415.30, "A": 440.00, "A#": 466.16, "B": 493.88,
}

# Patrones de batería Techno (1 = golpe, 0 = silencio, 16 pasos = 1 compás)
KICK_PATTERNS = {
    "soft":  [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],  # 4/4 básico
    "peak":  [1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0],  # Con anticipaciones
    "hard":  [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],  # Full kick (gabber-ish)
}

HIHAT_PATTERNS = {
    "soft":  [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0],  # Hi-hat abierto en 2 y 4
    "peak":  [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],  # 8ths
    "hard":  [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],  # 16ths agresivo
}

SNARE_PATTERNS = {
    "soft":  [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],  # 2 y 4
    "peak":  [0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0],  # Syncopado
    "hard":  [0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 1, 1],  # Industrial
}

# Secuencias de bajo por modo (intervalos en semitonos desde la tónica)
BASS_SEQUENCES = {
    "soft":  [0, 0, 7, 0, 5, 0, 7, 5],     # Tónica + quinta + cuarta
    "peak":  [0, 0, 0, 7, 0, 5, 3, 7],     # Más movimiento
    "hard":  [0, 12, 0, 7, 10, 7, 5, 0],  # Octavas y tensiones
}


class TechnoGenerator:
    """
    Generador de elementos musicales Techno mediante síntesis de audio.
    """

    def __init__(self, sample_rate: int = SAMPLE_RATE):
        self.sr = sample_rate

    # ── API pública ───────────────────────────────────────────────────

    def generate_all(
        self,
        output_dir: Path,
        bpm: float,
        musical_key: str,
        mode: str,
        duration_seconds: float,
    ) -> dict[str, Path]:
        """
        Genera todos los elementos Techno y los guarda en output_dir.

        Returns:
            Dict con rutas a los archivos generados
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        duration_samples = int(duration_seconds * self.sr)

        log.info(
            "Generating techno elements",
            bpm=bpm,
            key=musical_key,
            mode=mode,
            duration=duration_seconds,
        )

        results = {}

        # Batería completa
        kick = self.generate_kick(bpm, duration_samples, mode)
        hihat = self.generate_hihat(bpm, duration_samples, mode)
        snare = self.generate_snare(bpm, duration_samples, mode)

        # Mezclar batería
        drums = np.clip(kick * 0.9 + hihat * 0.5 + snare * 0.7, -1.0, 1.0)
        drums_path = output_dir / "techno_drums.wav"
        sf.write(str(drums_path), drums, self.sr)
        results["drums"] = drums_path
        log.info("Drums generated", path=str(drums_path))

        # Bajo Techno
        bass = self.generate_bass(bpm, musical_key, duration_samples, mode)
        bass_path = output_dir / "techno_bass.wav"
        sf.write(str(bass_path), bass, self.sr)
        results["bass"] = bass_path
        log.info("Bass generated")

        # Sintetizador/Pad
        synth = self.generate_synth_pad(bpm, musical_key, duration_samples, mode)
        synth_path = output_dir / "techno_synth.wav"
        sf.write(str(synth_path), synth, self.sr)
        results["synth"] = synth_path
        log.info("Synth generated")

        # Riser de tensión (opcional, para transiciones)
        riser = self.generate_riser(duration_samples)
        riser_path = output_dir / "techno_riser.wav"
        sf.write(str(riser_path), riser, self.sr)
        results["riser"] = riser_path

        return results

    # ── Batería ───────────────────────────────────────────────────────

    def generate_kick(self, bpm: float, n_samples: int, mode: str) -> np.ndarray:
        """
        Genera un kick drum Techno sintético.
        El kick Techno tiene: ataque de baja frecuencia (pitch bend) + body.
        """
        pattern = KICK_PATTERNS.get(mode, KICK_PATTERNS["peak"])
        step_samples = int(60.0 / bpm * self.sr / 4)  # 1 step = 1/16 nota

        output = np.zeros(n_samples)
        click_len = int(0.5 * self.sr)  # 500ms máximo por golpe

        for step_idx, hit in enumerate(pattern * (n_samples // (len(pattern) * step_samples) + 1)):
            if not hit:
                continue
            start = step_idx * step_samples
            if start >= n_samples:
                break

            end = min(start + click_len, n_samples)
            click_samples = end - start
            t = np.linspace(0, click_len / self.sr, click_len)[:click_samples]

            # Pitch envelope: de 150 Hz a 50 Hz en 150ms (kick clásico)
            freq_env = 150 * np.exp(-t * 20) + 50
            phase = 2 * np.pi * np.cumsum(freq_env / self.sr)
            kick_body = np.sin(phase)

            # Amplitud: ataque rápido, decaimiento exponencial
            amp_env = np.exp(-t * 12)

            output[start:end] += kick_body * amp_env

        # Normalizar
        max_val = np.max(np.abs(output)) + 1e-10
        return output / max_val

    def generate_hihat(self, bpm: float, n_samples: int, mode: str) -> np.ndarray:
        """
        Genera hi-hat usando ruido blanco filtrado y envolvente rápida.
        """
        pattern = HIHAT_PATTERNS.get(mode, HIHAT_PATTERNS["peak"])
        step_samples = int(60.0 / bpm * self.sr / 4)

        output = np.zeros(n_samples)
        rng = np.random.default_rng(42)

        for step_idx, hit in enumerate(pattern * (n_samples // (len(pattern) * step_samples) + 1)):
            if not hit:
                continue
            start = step_idx * step_samples
            if start >= n_samples:
                break

            hit_len = int(0.05 * self.sr)  # 50ms de hi-hat
            end = min(start + hit_len, n_samples)
            t = np.linspace(0, hit_len / self.sr, hit_len)[:end - start]

            noise = rng.uniform(-1, 1, len(t))
            amp = np.exp(-t * 80)  # Decaimiento muy rápido
            output[start:end] += noise * amp * 0.6

        max_val = np.max(np.abs(output)) + 1e-10
        return output / max_val

    def generate_snare(self, bpm: float, n_samples: int, mode: str) -> np.ndarray:
        """
        Genera snare/clap Techno: ruido + tono medio.
        """
        pattern = SNARE_PATTERNS.get(mode, SNARE_PATTERNS["peak"])
        step_samples = int(60.0 / bpm * self.sr / 4)

        output = np.zeros(n_samples)
        rng = np.random.default_rng(99)

        for step_idx, hit in enumerate(pattern * (n_samples // (len(pattern) * step_samples) + 1)):
            if not hit:
                continue
            start = step_idx * step_samples
            if start >= n_samples:
                break

            hit_len = int(0.15 * self.sr)
            end = min(start + hit_len, n_samples)
            t = np.linspace(0, hit_len / self.sr, hit_len)[:end - start]

            noise = rng.uniform(-1, 1, len(t))
            tone = np.sin(2 * np.pi * 200 * t)  # Tono de cuerpo
            amp = np.exp(-t * 30)
            output[start:end] += (noise * 0.7 + tone * 0.3) * amp

        max_val = np.max(np.abs(output)) + 1e-10
        return output / max_val

    # ── Bajo Techno ───────────────────────────────────────────────────

    def generate_bass(
        self,
        bpm: float,
        musical_key: str,
        n_samples: int,
        mode: str,
    ) -> np.ndarray:
        """
        Genera línea de bajo Techno: onda cuadrada/saw con filtro LP.
        """
        base_freq = NOTE_FREQUENCIES.get(musical_key, 440.0) / 4  # Una octava más baja
        sequence = BASS_SEQUENCES.get(mode, BASS_SEQUENCES["peak"])
        step_duration = 60.0 / bpm  # Un paso = 1 beat

        output = np.zeros(n_samples)
        step_samples = int(step_duration * self.sr)

        for step_idx in range(n_samples // step_samples + 1):
            note_semitones = sequence[step_idx % len(sequence)]
            freq = base_freq * (2 ** (note_semitones / 12))
            start = step_idx * step_samples
            end = min(start + step_samples, n_samples)
            t = np.linspace(0, step_samples / self.sr, step_samples)[:end - start]

            # Onda saw (sawtooth) - característica del bajo Techno
            wave = 2 * (t * freq - np.floor(t * freq + 0.5))

            # Envolvente corta para articulación
            env_len = min(len(t), int(0.01 * self.sr))
            env = np.ones(len(t))
            env[:env_len] = np.linspace(0, 1, env_len)  # Attack
            env[-env_len:] *= np.linspace(1, 0.3, env_len)  # Release

            output[start:end] += wave * env * 0.5

        # Filtro low-pass simple (media móvil) para suavizar armónicos
        kernel = np.ones(8) / 8
        output = np.convolve(output, kernel, mode="same")

        max_val = np.max(np.abs(output)) + 1e-10
        return np.clip(output / max_val * 0.8, -1.0, 1.0)

    # ── Sintetizador/Pad ──────────────────────────────────────────────

    def generate_synth_pad(
        self,
        bpm: float,
        musical_key: str,
        n_samples: int,
        mode: str,
    ) -> np.ndarray:
        """
        Genera un pad/lead sintetizador: acordes en la tonalidad.
        """
        root_freq = NOTE_FREQUENCIES.get(musical_key, 440.0) / 2

        # Acorde en la tonalidad (tríada mayor o menor + 7a)
        chord_intervals = [0, 4, 7, 11] if mode != "hard" else [0, 3, 7, 10]
        chord_freqs = [root_freq * (2 ** (i / 12)) for i in chord_intervals]

        t = np.linspace(0, n_samples / self.sr, n_samples)
        output = np.zeros(n_samples)

        for freq in chord_freqs:
            # Mezcla de ondas: seno + algo de saw para carácter Techno
            sine = np.sin(2 * np.pi * freq * t)
            saw = 2 * (t * freq - np.floor(t * freq + 0.5))
            output += sine * 0.6 + saw * 0.4

        # Modulación LFO lenta para movimiento
        lfo_rate = bpm / 60 / 8  # LFO a 1/8 del tempo
        lfo = 0.3 * np.sin(2 * np.pi * lfo_rate * t) + 0.7

        output *= lfo

        # Normalizar
        max_val = np.max(np.abs(output)) + 1e-10
        return np.clip(output / max_val * 0.35, -1.0, 1.0)

    # ── Riser ─────────────────────────────────────────────────────────

    def generate_riser(self, n_samples: int) -> np.ndarray:
        """
        Genera un riser de tensión (sweep de frecuencias ascendente).
        Útil para transiciones entre secciones.
        """
        t = np.linspace(0, n_samples / self.sr, n_samples)

        # Frecuencia que sube exponencialmente
        freq = 100 * np.exp(t * 2)

        # Limitar a rango audible
        freq = np.clip(freq, 100, 8000)

        phase = 2 * np.pi * np.cumsum(freq / self.sr)
        noise = np.random.default_rng(7).uniform(-0.1, 0.1, n_samples)

        output = (np.sin(phase) + noise) * np.linspace(0, 0.3, n_samples)

        max_val = np.max(np.abs(output)) + 1e-10
        return np.clip(output / max_val * 0.3, -1.0, 1.0)
