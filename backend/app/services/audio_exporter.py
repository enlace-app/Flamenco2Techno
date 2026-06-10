"""
Servicio de mezcla final y exportación de audio.
Aplica efectos con Pedalboard (Spotify) y exporta con FFmpeg.
"""

import subprocess
from pathlib import Path
from typing import Optional

import numpy as np
import soundfile as sf
import structlog

try:
    from pedalboard import (
        Pedalboard,
        Compressor,
        Reverb,
        Delay,
        LowpassFilter,
        HighpassFilter,
        Distortion,
        Limiter,
        PitchShift,
    )
    PEDALBOARD_AVAILABLE = True
except ImportError:
    PEDALBOARD_AVAILABLE = False

from app.config import settings

log = structlog.get_logger(__name__)


class AudioExporter:
    """
    Mezcla los stems procesados y los elementos Techno generados,
    aplica efectos de mastering y exporta el archivo final.
    """

    def __init__(self, sample_rate: int = settings.SAMPLE_RATE):
        self.sr = sample_rate

    def mix_and_export(
        self,
        vocals_path: Optional[Path],
        original_other_path: Optional[Path],
        techno_drums_path: Path,
        techno_bass_path: Path,
        techno_synth_path: Path,
        output_path: Path,
        mode: str,
        keep_vocals: bool,
        duration_seconds: float,
        export_format: str = "mp3",
    ) -> Path:
        """
        Mezcla final de todos los elementos y exportación.

        Args:
            vocals_path: Stem de voz de Demucs (opcional)
            original_other_path: Stem "other" de Demucs (melodía)
            techno_drums_path: Batería Techno generada
            techno_bass_path: Bajo Techno generado
            techno_synth_path: Sintetizador Techno generado
            output_path: Ruta del archivo de salida (sin extensión)
            mode: soft | peak | hard
            keep_vocals: Si incluir la voz original
            duration_seconds: Duración objetivo
            export_format: mp3 | wav

        Returns:
            Path al archivo de audio final exportado
        """
        n_samples = int(duration_seconds * self.sr)
        log.info("Starting mix", mode=mode, duration=duration_seconds, format=export_format)

        # ── Cargar y normalizar cada track ────────────────────────────
        def load_track(path: Optional[Path], target_len: int) -> np.ndarray:
            if path is None or not path.exists():
                return np.zeros(target_len)
            try:
                audio, file_sr = sf.read(str(path), always_2d=False)
                if len(audio.shape) > 1:
                    audio = np.mean(audio, axis=1)  # Convertir a mono
                if len(audio) > target_len:
                    audio = audio[:target_len]
                elif len(audio) < target_len:
                    audio = np.pad(audio, (0, target_len - len(audio)))
                return audio
            except Exception as e:
                log.warning("Failed to load track", path=str(path), error=str(e))
                return np.zeros(target_len)

        vocals = load_track(vocals_path, n_samples) if keep_vocals else np.zeros(n_samples)
        other = load_track(original_other_path, n_samples)
        drums = load_track(techno_drums_path, n_samples)
        bass = load_track(techno_bass_path, n_samples)
        synth = load_track(techno_synth_path, n_samples)

        # ── Niveles de mezcla por modo ────────────────────────────────
        levels = self._get_mix_levels(mode, keep_vocals)

        mix = (
            vocals * levels["vocals"] +
            other * levels["other"] +
            drums * levels["drums"] +
            bass * levels["bass"] +
            synth * levels["synth"]
        )

        # ── Aplicar efectos de mastering ──────────────────────────────
        mix = self._apply_effects(mix, mode)

        # ── Aplicar limiting final (evitar clipping) ──────────────────
        mix = self._apply_limiter(mix)

        # ── Guardar WAV temporal ──────────────────────────────────────
        temp_wav = output_path.parent / f"{output_path.stem}_temp.wav"
        sf.write(str(temp_wav), mix, self.sr, subtype="PCM_16")
        log.info("Temp WAV written", path=str(temp_wav))

        # ── Exportar con FFmpeg ───────────────────────────────────────
        final_path = self._export_with_ffmpeg(temp_wav, output_path, export_format, mode)

        # Limpiar WAV temporal
        temp_wav.unlink(missing_ok=True)

        log.info(
            "Export complete",
            output=str(final_path),
            size_mb=final_path.stat().st_size / 1e6,
        )

        return final_path

    def _get_mix_levels(self, mode: str, keep_vocals: bool) -> dict[str, float]:
        """Niveles de mezcla según el modo Techno."""
        levels = {
            "soft": {
                "vocals": 0.7,
                "other":  0.25,
                "drums":  0.65,
                "bass":   0.55,
                "synth":  0.35,
            },
            "peak": {
                "vocals": 0.6,
                "other":  0.15,
                "drums":  0.80,
                "bass":   0.65,
                "synth":  0.30,
            },
            "hard": {
                "vocals": 0.45,
                "other":  0.10,
                "drums":  0.90,
                "bass":   0.70,
                "synth":  0.20,
            },
        }
        mix = levels.get(mode, levels["peak"]).copy()
        if not keep_vocals:
            mix["vocals"] = 0.0
        return mix

    def _apply_effects(self, audio: np.ndarray, mode: str) -> np.ndarray:
        """
        Aplica efectos de procesamiento con Pedalboard.
        Si Pedalboard no está disponible, aplica efectos básicos en numpy.
        """
        if PEDALBOARD_AVAILABLE:
            return self._apply_pedalboard_effects(audio, mode)
        else:
            return self._apply_numpy_effects(audio, mode)

    def _apply_pedalboard_effects(self, audio: np.ndarray, mode: str) -> np.ndarray:
        """Cadena de efectos usando Pedalboard de Spotify."""
        # Configuración de efectos por modo
        if mode == "soft":
            board = Pedalboard([
                HighpassFilter(cutoff_frequency_hz=40),
                Compressor(threshold_db=-18, ratio=3.0, attack_ms=5, release_ms=100),
                Reverb(room_size=0.3, damping=0.7, wet_level=0.15),
                Limiter(threshold_db=-1.0),
            ])
        elif mode == "peak":
            board = Pedalboard([
                HighpassFilter(cutoff_frequency_hz=30),
                Compressor(threshold_db=-12, ratio=4.0, attack_ms=3, release_ms=80),
                Reverb(room_size=0.2, damping=0.8, wet_level=0.1),
                Limiter(threshold_db=-0.5),
            ])
        else:  # hard
            board = Pedalboard([
                HighpassFilter(cutoff_frequency_hz=25),
                Distortion(drive_db=8),
                Compressor(threshold_db=-10, ratio=6.0, attack_ms=2, release_ms=50),
                Reverb(room_size=0.15, damping=0.9, wet_level=0.05),
                Limiter(threshold_db=-0.1),
            ])

        # Pedalboard trabaja con float32 y necesita forma (canales, muestras)
        audio_f32 = audio.astype(np.float32)
        processed = board(audio_f32, self.sr)
        return processed.astype(np.float64)

    def _apply_numpy_effects(self, audio: np.ndarray, mode: str) -> np.ndarray:
        """
        Efectos básicos implementados con numpy (fallback sin Pedalboard).
        """
        # Compresión simple: reducir picos por encima del umbral
        threshold = 0.7
        ratio = 4.0 if mode == "hard" else 3.0

        peaks = np.abs(audio) > threshold
        audio[peaks] = np.sign(audio[peaks]) * (
            threshold + (np.abs(audio[peaks]) - threshold) / ratio
        )

        # High-pass filter básico (eliminar DC y sub-graves < 20 Hz)
        # Implementado como diferencia de primer orden
        hp_coeff = 0.99
        filtered = np.zeros_like(audio)
        filtered[0] = audio[0]
        for i in range(1, len(audio)):
            filtered[i] = hp_coeff * (filtered[i-1] + audio[i] - audio[i-1])

        return filtered

    def _apply_limiter(self, audio: np.ndarray, ceiling: float = 0.95) -> np.ndarray:
        """Limiter final: evita clipping y normaliza al nivel objetivo."""
        max_val = np.max(np.abs(audio))
        if max_val > 1e-10:
            audio = audio / max_val * ceiling
        return np.clip(audio, -1.0, 1.0)

    def _export_with_ffmpeg(
        self,
        input_wav: Path,
        output_path: Path,
        export_format: str,
        mode: str,
    ) -> Path:
        """
        Usa FFmpeg para exportar al formato final con los metadatos correctos.
        """
        if export_format == "mp3":
            final_path = output_path.with_suffix(".mp3")
            cmd = [
                "ffmpeg", "-y",
                "-i", str(input_wav),
                "-vn",
                "-ar", str(self.sr),
                "-ac", "2",                           # Estéreo
                "-b:a", settings.EXPORT_MP3_BITRATE,  # 320k
                "-codec:a", "libmp3lame",
                "-id3v2_version", "3",
                "-metadata", "comment=Generated by Flamenco2Techno AI",
                "-metadata", f"genre=Techno ({mode})",
                str(final_path),
            ]
        else:  # wav
            final_path = output_path.with_suffix(".wav")
            cmd = [
                "ffmpeg", "-y",
                "-i", str(input_wav),
                "-vn",
                "-ar", str(self.sr),
                "-ac", "2",
                "-codec:a", "pcm_s16le",  # WAV 16-bit
                str(final_path),
            ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )

            if result.returncode != 0:
                log.error("FFmpeg failed", stderr=result.stderr[:300])
                raise RuntimeError(f"FFmpeg error: {result.stderr[:200]}")

        except subprocess.TimeoutExpired:
            raise RuntimeError("FFmpeg timeout durante exportación")

        return final_path

    def adjust_tempo(self, audio: np.ndarray, original_bpm: float, target_bpm: float) -> np.ndarray:
        """
        Ajusta el tempo del audio usando time-stretching con librosa.
        Ratio: target_bpm / original_bpm

        Args:
            audio: Array de audio
            original_bpm: BPM original detectado
            target_bpm: BPM objetivo (125-140)

        Returns:
            Audio con tempo ajustado
        """
        if abs(original_bpm - target_bpm) < 1.0:
            return audio  # No necesita ajuste

        try:
            import librosa
            ratio = target_bpm / original_bpm
            log.info(
                "Adjusting tempo",
                original=original_bpm,
                target=target_bpm,
                ratio=round(ratio, 3),
            )
            stretched = librosa.effects.time_stretch(audio.astype(np.float32), rate=ratio)
            return stretched.astype(np.float64)
        except Exception as e:
            log.warning("Tempo adjustment failed, using original", error=str(e))
            return audio
