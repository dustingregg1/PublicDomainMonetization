"""
Audiobook Packaging Module

Creates final distribution-ready audiobook files:
- Combined MP3 with ID3 tags
- M4B with chapter markers
- Metadata JSON
- Distribution package
"""

import json
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ChapterMeta:
    """Metadata for a single chapter."""
    number: int
    title: str
    file_path: Path
    duration_seconds: float = 0.0
    start_time_seconds: float = 0.0


@dataclass
class BookMeta:
    """Book metadata for packaging."""
    title: str
    author: str
    narrator: str = "AI Narration"
    year: str = "2026"
    genre: str = "Science Fiction"
    description: str = ""
    cover_art_path: Optional[Path] = None
    isbn: Optional[str] = None
    disclaimer: str = ""


class AudiobookPackager:
    """
    Package mastered audio into distribution formats.

    Creates:
    - Individual MP3 chapters with proper ID3 tags
    - Combined single-file MP3
    - M4B audiobook with chapter markers (requires ffmpeg)
    - metadata.json for platform uploads
    """

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def package_audiobook(
        self,
        mastered_dir: Path,
        book_meta: BookMeta,
        chapter_titles: Optional[List[str]] = None,
    ) -> Dict[str, Path]:
        """
        Create all distribution formats from mastered chapters.

        Args:
            mastered_dir: Directory with mastered chapter WAVs
            book_meta: Book metadata
            chapter_titles: Optional list of chapter titles

        Returns:
            Dict mapping format name to file path
        """
        chapter_files = sorted(mastered_dir.glob("chapter_*.wav"))
        if not chapter_files:
            raise FileNotFoundError(
                f"No mastered chapter files in {mastered_dir}"
            )

        # Build chapter metadata
        chapters = []
        for i, f in enumerate(chapter_files):
            title = (
                chapter_titles[i]
                if chapter_titles and i < len(chapter_titles)
                else f"Chapter {i + 1}"
            )
            chapters.append(
                ChapterMeta(
                    number=i + 1,
                    title=title,
                    file_path=f,
                )
            )

        outputs = {}

        # Create individual MP3 chapters
        mp3_dir = self.output_dir / "mp3_chapters"
        mp3_dir.mkdir(exist_ok=True)
        mp3_files = self._create_mp3_chapters(chapters, book_meta, mp3_dir)
        outputs["mp3_chapters"] = mp3_dir

        # Create combined MP3
        combined_mp3 = self.output_dir / f"{self._safe_filename(book_meta.title)}.mp3"
        self._create_combined_mp3(mp3_files, combined_mp3, book_meta)
        outputs["combined_mp3"] = combined_mp3

        # Create M4B with chapters
        m4b_path = self.output_dir / f"{self._safe_filename(book_meta.title)}.m4b"
        self._create_m4b(chapter_files, chapters, m4b_path, book_meta)
        outputs["m4b"] = m4b_path

        # Create metadata JSON
        metadata_path = self.output_dir / "metadata.json"
        self._create_metadata(chapters, book_meta, metadata_path, outputs)
        outputs["metadata"] = metadata_path

        logger.info(
            f"Packaging complete: {len(outputs)} outputs in {self.output_dir}"
        )
        return outputs

    def _create_mp3_chapters(
        self,
        chapters: List[ChapterMeta],
        book_meta: BookMeta,
        output_dir: Path,
    ) -> List[Path]:
        """Convert chapters to tagged MP3 files."""
        mp3_files = []

        for ch in chapters:
            mp3_path = output_dir / f"{ch.number:02d}_{self._safe_filename(ch.title)}.mp3"

            # Use ffmpeg to convert WAV to MP3 with metadata
            cmd = [
                "ffmpeg", "-y",
                "-i", str(ch.file_path),
                "-codec:a", "libmp3lame",
                "-b:a", "192k",
                "-metadata", f"title={ch.title}",
                "-metadata", f"artist={book_meta.narrator}",
                "-metadata", f"album={book_meta.title}",
                "-metadata", f"album_artist={book_meta.author}",
                "-metadata", f"track={ch.number}/{len(chapters)}",
                "-metadata", f"genre={book_meta.genre}",
                "-metadata", f"date={book_meta.year}",
            ]

            # Add cover art if available
            if book_meta.cover_art_path and book_meta.cover_art_path.exists():
                cmd.extend([
                    "-i", str(book_meta.cover_art_path),
                    "-map", "0:a", "-map", "1:v",
                    "-c:v", "mjpeg",
                    "-metadata:s:v", "title=Album cover",
                    "-metadata:s:v", "comment=Cover (front)",
                ])

            cmd.append(str(mp3_path))

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                if result.returncode != 0:
                    logger.error(f"ffmpeg error for {ch.title}: {result.stderr}")
                else:
                    mp3_files.append(mp3_path)
                    logger.info(f"  MP3: {mp3_path.name}")
            except FileNotFoundError:
                logger.error(
                    "ffmpeg not found. Install with: apt install ffmpeg"
                )
                raise
            except subprocess.TimeoutExpired:
                logger.error(f"ffmpeg timeout for chapter {ch.number}")

        return mp3_files

    def _create_combined_mp3(
        self,
        mp3_files: List[Path],
        output_path: Path,
        book_meta: BookMeta,
    ) -> None:
        """Combine individual MP3s into single file."""
        if not mp3_files:
            logger.warning("No MP3 files to combine")
            return

        # Create file list for ffmpeg concat
        list_file = output_path.parent / ".concat_list.txt"
        with open(list_file, "w") as f:
            for mp3 in mp3_files:
                f.write(f"file '{mp3}'\n")

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_file),
            "-c", "copy",
            "-metadata", f"title={book_meta.title}",
            "-metadata", f"artist={book_meta.author}",
            "-metadata", f"album={book_meta.title}",
            str(output_path),
        ]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300
            )
            if result.returncode == 0:
                logger.info(f"Combined MP3: {output_path}")
            else:
                logger.error(f"ffmpeg concat error: {result.stderr}")
        except Exception as e:
            logger.error(f"Failed to create combined MP3: {e}")
        finally:
            list_file.unlink(missing_ok=True)

    def _create_m4b(
        self,
        chapter_files: List[Path],
        chapters: List[ChapterMeta],
        output_path: Path,
        book_meta: BookMeta,
    ) -> None:
        """Create M4B audiobook with chapter markers."""
        if not chapter_files:
            return

        # First concatenate all WAVs
        concat_wav = output_path.parent / ".concat_temp.wav"
        list_file = output_path.parent / ".m4b_concat_list.txt"

        with open(list_file, "w") as f:
            for wav in chapter_files:
                f.write(f"file '{wav}'\n")

        try:
            # Concatenate WAVs
            result = subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-f", "concat", "-safe", "0",
                    "-i", str(list_file),
                    "-c", "copy",
                    str(concat_wav),
                ],
                capture_output=True, text=True, timeout=300,
            )

            if result.returncode != 0:
                logger.error(f"WAV concat failed: {result.stderr}")
                return

            # Create chapter metadata file for ffmpeg
            chapters_file = output_path.parent / ".chapters.txt"
            self._write_ffmpeg_chapters(chapters, chapter_files, chapters_file)

            # Convert to M4B with chapters
            cmd = [
                "ffmpeg", "-y",
                "-i", str(concat_wav),
                "-i", str(chapters_file),
                "-map_metadata", "1",
                "-codec:a", "aac",
                "-b:a", "128k",
                "-f", "mp4",
                "-metadata", f"title={book_meta.title}",
                "-metadata", f"artist={book_meta.author}",
                "-metadata", f"album={book_meta.title}",
                str(output_path),
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=600
            )

            if result.returncode == 0:
                logger.info(f"M4B: {output_path}")
            else:
                logger.error(f"M4B creation failed: {result.stderr}")
                # Fallback: just convert without chapter markers
                self._create_m4b_simple(concat_wav, output_path, book_meta)

        except FileNotFoundError:
            logger.error("ffmpeg not found for M4B creation")
        finally:
            concat_wav.unlink(missing_ok=True)
            list_file.unlink(missing_ok=True)
            chapters_file = output_path.parent / ".chapters.txt"
            chapters_file.unlink(missing_ok=True)

    def _create_m4b_simple(
        self, input_wav: Path, output_path: Path, book_meta: BookMeta
    ) -> None:
        """Simple M4B without chapter markers (fallback)."""
        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_wav),
            "-codec:a", "aac",
            "-b:a", "128k",
            "-f", "mp4",
            "-metadata", f"title={book_meta.title}",
            "-metadata", f"artist={book_meta.author}",
            str(output_path),
        ]
        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            logger.info(f"M4B (simple): {output_path}")
        except Exception as e:
            logger.error(f"Simple M4B failed: {e}")

    def _write_ffmpeg_chapters(
        self,
        chapters: List[ChapterMeta],
        chapter_files: List[Path],
        output_file: Path,
    ) -> None:
        """Write ffmpeg-format chapter metadata."""
        import wave

        lines = [";FFMETADATA1"]
        current_time_ms = 0

        for i, (ch, wav_path) in enumerate(zip(chapters, chapter_files)):
            # Get duration from WAV file
            try:
                with wave.open(str(wav_path), "rb") as wf:
                    duration_ms = int(
                        (wf.getnframes() / wf.getframerate()) * 1000
                    )
            except Exception:
                duration_ms = 300000  # 5 min fallback

            ch.duration_seconds = duration_ms / 1000
            ch.start_time_seconds = current_time_ms / 1000

            lines.append("[CHAPTER]")
            lines.append("TIMEBASE=1/1000")
            lines.append(f"START={current_time_ms}")
            lines.append(f"END={current_time_ms + duration_ms}")
            lines.append(f"title={ch.title}")

            current_time_ms += duration_ms

        output_file.write_text("\n".join(lines), encoding="utf-8")

    def _create_metadata(
        self,
        chapters: List[ChapterMeta],
        book_meta: BookMeta,
        output_path: Path,
        file_outputs: Dict[str, Path],
    ) -> None:
        """Create metadata JSON for platform uploads."""
        total_duration = sum(ch.duration_seconds for ch in chapters)

        metadata = {
            "title": book_meta.title,
            "author": book_meta.author,
            "narrator": book_meta.narrator,
            "year": book_meta.year,
            "genre": book_meta.genre,
            "description": book_meta.description,
            "disclaimer": book_meta.disclaimer,
            "total_duration_seconds": total_duration,
            "total_duration_hours": total_duration / 3600,
            "total_chapters": len(chapters),
            "chapters": [
                {
                    "number": ch.number,
                    "title": ch.title,
                    "duration_seconds": ch.duration_seconds,
                    "start_time_seconds": ch.start_time_seconds,
                }
                for ch in chapters
            ],
            "files": {
                name: str(path)
                for name, path in file_outputs.items()
            },
            "production": {
                "tts_engine": "Coqui XTTS-v2",
                "mastering": "Custom audiobook pipeline",
                "format_mp3_bitrate": "192kbps",
                "format_m4b_bitrate": "128kbps",
            },
        }

        output_path.write_text(
            json.dumps(metadata, indent=2),
            encoding="utf-8",
        )
        logger.info(f"Metadata: {output_path}")

    @staticmethod
    def _safe_filename(name: str) -> str:
        """Convert string to safe filename."""
        import re
        safe = re.sub(r"[^\w\s-]", "", name)
        safe = re.sub(r"\s+", "_", safe)
        return safe.lower().strip("_")
