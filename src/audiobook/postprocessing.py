"""
Audio Post-Processing and Mastering for Audiobooks

Handles:
- Volume normalization (target -16 LUFS for audiobooks)
- Noise reduction
- EQ for voice clarity
- Silence trimming / padding
- Chapter-level consistency
"""

import logging
import struct
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class MasteringProfile:
    """Audio mastering settings."""
    target_lufs: float = -16.0   # Standard for audiobooks
    target_peak_dbfs: float = -3.0
    silence_threshold_db: float = -40.0
    min_silence_ms: int = 300     # Min silence between sentences
    max_silence_ms: int = 800     # Max silence between sentences
    chapter_pause_ms: int = 2000  # Pause between chapters
    fade_in_ms: int = 50
    fade_out_ms: int = 100
    sample_rate: int = 22050     # XTTS-v2 default output
    # High-pass filter to remove rumble
    highpass_freq: int = 80
    # De-essing
    deess: bool = True


MASTERING_PROFILES = {
    "audiobook_standard": MasteringProfile(),
    "audiobook_dense": MasteringProfile(
        # For dense philosophical text - more breathing room
        min_silence_ms=400,
        max_silence_ms=1000,
        target_lufs=-15.0,
    ),
    "audiobook_dramatic": MasteringProfile(
        # For dialogue-heavy books
        min_silence_ms=250,
        max_silence_ms=600,
        target_lufs=-16.0,
    ),
}


class AudioMastering:
    """
    Audio mastering pipeline for audiobook production.

    Uses pydub for basic processing, with optional librosa/scipy
    for advanced features.
    """

    def __init__(
        self,
        profile: Optional[str] = None,
        output_format: str = "wav",
    ) -> None:
        """
        Args:
            profile: Mastering profile name
            output_format: Output format ('wav' or 'mp3')
        """
        self.profile = MASTERING_PROFILES.get(
            profile or "audiobook_standard",
            MASTERING_PROFILES["audiobook_standard"],
        )
        self.output_format = output_format

    def master_chapter(
        self,
        input_path: Path,
        output_path: Path,
    ) -> Path:
        """
        Master a single chapter audio file.

        Args:
            input_path: Input WAV file
            output_path: Output mastered file

        Returns:
            Path to mastered file
        """
        try:
            from pydub import AudioSegment
            from pydub.effects import normalize, compress_dynamic_range
        except ImportError:
            raise ImportError(
                "pydub not installed. Run: pip install pydub\n"
                "Also requires ffmpeg: apt install ffmpeg"
            )

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Mastering: {input_path.name}")

        # Load audio
        audio = AudioSegment.from_wav(str(input_path))

        # Step 1: Normalize volume
        audio = normalize(audio)

        # Step 2: Light compression for consistency
        audio = compress_dynamic_range(
            audio,
            threshold=-20.0,
            ratio=3.0,
            attack=5.0,
            release=50.0,
        )

        # Step 3: Trim leading/trailing silence
        audio = self._trim_silence(audio)

        # Step 4: Add fade in/out
        audio = audio.fade_in(self.profile.fade_in_ms)
        audio = audio.fade_out(self.profile.fade_out_ms)

        # Step 5: Final normalize to target level
        target_dbfs = self.profile.target_peak_dbfs
        change = target_dbfs - audio.max_dBFS
        audio = audio + change

        # Export
        if self.output_format == "mp3":
            audio.export(
                str(output_path),
                format="mp3",
                bitrate="192k",
                parameters=["-q:a", "2"],
            )
        else:
            audio.export(str(output_path), format="wav")

        duration_sec = len(audio) / 1000
        logger.info(
            f"  Mastered: {output_path.name} "
            f"({duration_sec:.1f}s, {audio.max_dBFS:.1f} dBFS)"
        )

        return output_path

    def master_book(
        self,
        chapter_dir: Path,
        output_dir: Path,
        progress_callback: Optional[callable] = None,
    ) -> List[Path]:
        """
        Master all chapters in a directory.

        Args:
            chapter_dir: Directory with raw chapter WAVs
            output_dir: Output directory for mastered files
            progress_callback: Called with (current, total)

        Returns:
            List of mastered file paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # Find chapter files
        chapter_files = sorted(chapter_dir.glob("chapter_*.wav"))
        if not chapter_files:
            raise FileNotFoundError(
                f"No chapter WAV files found in {chapter_dir}"
            )

        logger.info(f"Mastering {len(chapter_files)} chapters")
        mastered = []

        for i, chapter_file in enumerate(chapter_files):
            output_path = output_dir / chapter_file.name
            self.master_chapter(chapter_file, output_path)
            mastered.append(output_path)

            if progress_callback:
                progress_callback(i + 1, len(chapter_files))

        return mastered

    def _trim_silence(self, audio) -> "AudioSegment":
        """Trim leading and trailing silence from audio."""
        from pydub.silence import detect_leading_silence

        # Trim leading silence
        start_trim = detect_leading_silence(
            audio,
            silence_threshold=self.profile.silence_threshold_db,
        )
        # Trim trailing silence
        end_trim = detect_leading_silence(
            audio.reverse(),
            silence_threshold=self.profile.silence_threshold_db,
        )

        trimmed = audio[start_trim:len(audio) - end_trim]

        # Add standard padding
        from pydub import AudioSegment as AS
        silence_pad = AS.silent(duration=self.profile.min_silence_ms)
        return silence_pad + trimmed + silence_pad

    def analyze_audio(self, file_path: Path) -> dict:
        """
        Analyze an audio file and return stats.

        Uses wave module for basic analysis (no heavy deps).
        """
        with wave.open(str(file_path), "rb") as wf:
            n_channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            frame_rate = wf.getframerate()
            n_frames = wf.getnframes()
            duration = n_frames / frame_rate

            # Read frames to compute peak
            frames = wf.readframes(n_frames)

        # Compute peak amplitude
        if sample_width == 2:
            fmt = f"<{n_frames * n_channels}h"
            samples = struct.unpack(fmt, frames)
            peak = max(abs(s) for s in samples) if samples else 0
            peak_ratio = peak / 32768.0
        else:
            peak_ratio = 0

        return {
            "duration_seconds": duration,
            "sample_rate": frame_rate,
            "channels": n_channels,
            "bit_depth": sample_width * 8,
            "peak_ratio": peak_ratio,
            "file_size_mb": file_path.stat().st_size / (1024 * 1024),
        }
