"""
TTS Engine for Audiobook Production

Wraps Coqui XTTS-v2 for high-quality text-to-speech synthesis.
Optimized for RTX 5080 (16GB VRAM).

Voice profiles control pitch, speed, and style for different
book genres (hardboiled detective, philosophical SF, British golden age).
"""

import logging
import os
import re
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class VoiceProfile:
    """Configuration for a TTS voice."""
    name: str
    language: str = "en"
    speaker_wav: Optional[str] = None  # Reference audio for voice cloning
    speed: float = 1.0
    # Coqui XTTS-v2 specific settings
    temperature: float = 0.65
    top_p: float = 0.85
    top_k: int = 50
    repetition_penalty: float = 5.0


# Pre-configured voice profiles matching production kits
VOICE_PROFILES = {
    "philosophical_sf": VoiceProfile(
        name="Cosmic Chronicler",
        language="en",
        speed=0.92,  # Slightly slower for dense philosophical content
        temperature=0.6,  # More consistent, less random
        top_p=0.8,
    ),
    "hardboiled_detective": VoiceProfile(
        name="Hardboiled Narrator",
        language="en",
        speed=1.0,
        temperature=0.7,
        top_p=0.85,
    ),
    "golden_age_british": VoiceProfile(
        name="Golden Age British",
        language="en",
        speed=0.95,
        temperature=0.65,
        top_p=0.85,
    ),
    "default": VoiceProfile(
        name="Default Narrator",
        language="en",
        speed=1.0,
    ),
}


def _split_into_sentences(text: str) -> List[str]:
    """Split text into sentences for TTS processing."""
    # Split on sentence boundaries, keeping the delimiter
    parts = re.split(r"(?<=[.!?])\s+", text)
    sentences = []
    current = ""

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Accumulate short sentences to avoid tiny audio clips
        if len(current) + len(part) < 250:
            current = f"{current} {part}".strip() if current else part
        else:
            if current:
                sentences.append(current)
            current = part

    if current:
        sentences.append(current)

    return sentences


def _split_into_chunks(text: str, max_chars: int = 500) -> List[str]:
    """
    Split text into chunks suitable for TTS processing.

    XTTS-v2 works best with chunks of ~200-500 characters.
    Split on sentence boundaries where possible.
    """
    sentences = _split_into_sentences(text)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 > max_chars:
            if current_chunk:
                chunks.append(current_chunk.strip())
            # Handle sentences longer than max_chars
            if len(sentence) > max_chars:
                words = sentence.split()
                sub_chunk = ""
                for word in words:
                    if len(sub_chunk) + len(word) + 1 > max_chars:
                        if sub_chunk:
                            chunks.append(sub_chunk.strip())
                        sub_chunk = word
                    else:
                        sub_chunk = f"{sub_chunk} {word}".strip()
                current_chunk = sub_chunk
            else:
                current_chunk = sentence
        else:
            current_chunk = f"{current_chunk} {sentence}".strip()

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


class TTSEngine:
    """
    Text-to-Speech engine using Coqui XTTS-v2.

    Handles:
    - Loading model to GPU
    - Text chunking for optimal synthesis
    - Voice profile application
    - WAV file output per chapter
    - Progress tracking
    """

    def __init__(
        self,
        model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2",
        device: str = "auto",
        voice_profile: Optional[str] = None,
    ) -> None:
        """
        Initialize TTS engine.

        Args:
            model_name: Coqui TTS model identifier
            device: 'cuda', 'cpu', or 'auto'
            voice_profile: Name of voice profile to use
        """
        self.model_name = model_name
        self.device = device
        self.profile = VOICE_PROFILES.get(
            voice_profile or "default", VOICE_PROFILES["default"]
        )
        self._tts = None
        self._loaded = False

    def load_model(self) -> None:
        """Load TTS model to GPU/CPU."""
        if self._loaded:
            return

        try:
            from TTS.api import TTS
        except ImportError:
            raise ImportError(
                "Coqui TTS not installed. Run: pip install TTS\n"
                "For GPU support: pip install TTS torch torchvision torchaudio "
                "--index-url https://download.pytorch.org/whl/cu121"
            )

        device = self.device
        if device == "auto":
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"

        logger.info(f"Loading TTS model '{self.model_name}' on {device}")
        self._tts = TTS(model_name=self.model_name).to(device)
        self._loaded = True
        logger.info("TTS model loaded successfully")

    def unload_model(self) -> None:
        """Unload model to free VRAM."""
        if self._tts is not None:
            del self._tts
            self._tts = None
            self._loaded = False

            # Free GPU memory
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass

            logger.info("TTS model unloaded")

    def synthesize_chapter(
        self,
        text: str,
        output_path: Path,
        speaker_wav: Optional[str] = None,
        progress_callback: Optional[callable] = None,
    ) -> Path:
        """
        Synthesize a full chapter to WAV.

        Args:
            text: Chapter text
            output_path: Output WAV file path
            speaker_wav: Optional reference audio for voice cloning
            progress_callback: Called with (current_chunk, total_chunks)

        Returns:
            Path to output WAV file
        """
        self.load_model()
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Clean text for TTS
        clean_text = self._clean_text_for_tts(text)

        # Split into chunks
        chunks = _split_into_chunks(clean_text, max_chars=500)
        total_chunks = len(chunks)

        logger.info(
            f"Synthesizing {total_chunks} chunks "
            f"({len(clean_text):,} chars)"
        )

        # Determine speaker reference
        ref_wav = speaker_wav or self.profile.speaker_wav

        # Synthesize each chunk and concatenate
        temp_dir = output_path.parent / ".tts_temp"
        temp_dir.mkdir(exist_ok=True)
        chunk_files = []

        try:
            for i, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue

                chunk_path = temp_dir / f"chunk_{i:04d}.wav"

                if ref_wav and os.path.exists(ref_wav):
                    # Voice cloning mode
                    self._tts.tts_to_file(
                        text=chunk,
                        file_path=str(chunk_path),
                        speaker_wav=ref_wav,
                        language=self.profile.language,
                        speed=self.profile.speed,
                    )
                else:
                    # Use default speaker
                    self._tts.tts_to_file(
                        text=chunk,
                        file_path=str(chunk_path),
                        language=self.profile.language,
                        speed=self.profile.speed,
                    )

                chunk_files.append(chunk_path)

                if progress_callback:
                    progress_callback(i + 1, total_chunks)

                if (i + 1) % 10 == 0:
                    logger.info(
                        f"  Progress: {i + 1}/{total_chunks} chunks "
                        f"({(i + 1) / total_chunks * 100:.0f}%)"
                    )

            # Concatenate all chunks into final WAV
            self._concatenate_wav_files(chunk_files, output_path)

            logger.info(f"Chapter synthesized: {output_path}")
            return output_path

        finally:
            # Clean up temp files
            for f in chunk_files:
                if f.exists():
                    f.unlink()
            if temp_dir.exists():
                try:
                    temp_dir.rmdir()
                except OSError:
                    pass

    def _clean_text_for_tts(self, text: str) -> str:
        """Clean text for TTS synthesis."""
        # Remove chapter headings that might have been included
        text = re.sub(r"^CHAPTER\s+[IVXLCDM\d]+.*?\n", "", text)

        # Convert em-dashes to pauses
        text = text.replace("—", " -- ")
        text = text.replace("–", " -- ")

        # Handle ellipsis
        text = text.replace("...", " ... ")

        # Remove excessive whitespace
        text = re.sub(r"\n{2,}", "\n", text)
        text = re.sub(r"  +", " ", text)

        # Remove any stray formatting
        text = re.sub(r"\[.*?\]", "", text)  # Remove [footnotes]
        text = re.sub(r"\{.*?\}", "", text)  # Remove {annotations}

        return text.strip()

    def _concatenate_wav_files(
        self, wav_files: List[Path], output_path: Path
    ) -> None:
        """Concatenate multiple WAV files into one."""
        if not wav_files:
            raise ValueError("No WAV files to concatenate")

        # Read first file to get params
        with wave.open(str(wav_files[0]), "rb") as first:
            params = first.getparams()

        # Write concatenated output
        with wave.open(str(output_path), "wb") as output:
            output.setparams(params)

            for wav_file in wav_files:
                with wave.open(str(wav_file), "rb") as chunk:
                    output.writeframes(chunk.readframes(chunk.getnframes()))

    def estimate_duration(self, text: str) -> float:
        """
        Estimate audio duration in seconds.

        Args:
            text: Input text

        Returns:
            Estimated duration in seconds
        """
        word_count = len(text.split())
        # Average narration speed: ~150 words per minute
        wpm = 150 * self.profile.speed
        return (word_count / wpm) * 60

    def get_profile_info(self) -> dict:
        """Get current voice profile info."""
        return {
            "name": self.profile.name,
            "language": self.profile.language,
            "speed": self.profile.speed,
            "temperature": self.profile.temperature,
            "has_speaker_ref": bool(self.profile.speaker_wav),
            "model": self.model_name,
        }
