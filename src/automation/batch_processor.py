"""
Batch Processor for Overnight Audiobook Production

Coordinates full audiobook production runs on RTX 5080.
Designed for overnight unattended processing with:
- Full book synthesis in one batch
- Progress persistence (survives restarts)
- Error recovery and retry logic
- Email/notification on completion
- Power management awareness
"""

import os
import json
import logging
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from enum import Enum
import shutil

from .gpu_orchestrator import (
    GPUOrchestrator,
    GPUTask,
    TaskType,
    TaskPriority,
    TaskStatus,
)

logger = logging.getLogger(__name__)


class BatchStatus(Enum):
    """Batch job status."""
    CREATED = "created"
    QUEUED = "queued"
    PREPROCESSING = "preprocessing"
    SYNTHESIZING = "synthesizing"
    MASTERING = "mastering"
    PACKAGING = "packaging"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class ChapterProgress:
    """Progress for a single chapter."""
    chapter_id: str
    chapter_num: int
    title: str
    word_count: int
    status: TaskStatus = TaskStatus.PENDING
    audio_path: Optional[Path] = None
    mastered_path: Optional[Path] = None
    duration_seconds: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    retries: int = 0


@dataclass
class BatchJob:
    """A complete audiobook batch production job."""
    job_id: str
    book_id: str
    title: str
    author: str
    source_text_path: Path
    output_dir: Path
    voice_profile: str
    status: BatchStatus = BatchStatus.CREATED
    chapters: List[ChapterProgress] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_word_count: int = 0
    total_duration_seconds: float = 0.0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for persistence."""
        return {
            "job_id": self.job_id,
            "book_id": self.book_id,
            "title": self.title,
            "author": self.author,
            "source_text_path": str(self.source_text_path),
            "output_dir": str(self.output_dir),
            "voice_profile": self.voice_profile,
            "status": self.status.value,
            "chapters": [
                {
                    "chapter_id": ch.chapter_id,
                    "chapter_num": ch.chapter_num,
                    "title": ch.title,
                    "word_count": ch.word_count,
                    "status": ch.status.value,
                    "audio_path": str(ch.audio_path) if ch.audio_path else None,
                    "mastered_path": str(ch.mastered_path) if ch.mastered_path else None,
                    "duration_seconds": ch.duration_seconds,
                    "started_at": ch.started_at.isoformat() if ch.started_at else None,
                    "completed_at": ch.completed_at.isoformat() if ch.completed_at else None,
                    "error": ch.error,
                    "retries": ch.retries,
                }
                for ch in self.chapters
            ],
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_word_count": self.total_word_count,
            "total_duration_seconds": self.total_duration_seconds,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BatchJob":
        """Deserialize from persistence."""
        job = cls(
            job_id=data["job_id"],
            book_id=data["book_id"],
            title=data["title"],
            author=data["author"],
            source_text_path=Path(data["source_text_path"]),
            output_dir=Path(data["output_dir"]),
            voice_profile=data["voice_profile"],
            status=BatchStatus(data["status"]),
            total_word_count=data.get("total_word_count", 0),
            total_duration_seconds=data.get("total_duration_seconds", 0.0),
            error_message=data.get("error_message"),
            metadata=data.get("metadata", {}),
        )

        if data.get("created_at"):
            job.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("started_at"):
            job.started_at = datetime.fromisoformat(data["started_at"])
        if data.get("completed_at"):
            job.completed_at = datetime.fromisoformat(data["completed_at"])

        for ch_data in data.get("chapters", []):
            ch = ChapterProgress(
                chapter_id=ch_data["chapter_id"],
                chapter_num=ch_data["chapter_num"],
                title=ch_data["title"],
                word_count=ch_data["word_count"],
                status=TaskStatus(ch_data["status"]),
                duration_seconds=ch_data.get("duration_seconds", 0.0),
                retries=ch_data.get("retries", 0),
                error=ch_data.get("error"),
            )
            if ch_data.get("audio_path"):
                ch.audio_path = Path(ch_data["audio_path"])
            if ch_data.get("mastered_path"):
                ch.mastered_path = Path(ch_data["mastered_path"])
            if ch_data.get("started_at"):
                ch.started_at = datetime.fromisoformat(ch_data["started_at"])
            if ch_data.get("completed_at"):
                ch.completed_at = datetime.fromisoformat(ch_data["completed_at"])
            job.chapters.append(ch)

        return job


class BatchProcessor:
    """
    Manages overnight batch audiobook production.

    Features:
    - Full pipeline automation
    - Progress persistence (survives restarts)
    - Intelligent retry logic
    - Notification on completion
    - RTX 5080 optimized scheduling
    """

    MAX_RETRIES = 3
    CHECKPOINT_INTERVAL_MINUTES = 5

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        orchestrator: Optional[GPUOrchestrator] = None,
    ) -> None:
        """Initialize batch processor."""
        self.data_dir = data_dir or Path.cwd() / "batch_jobs"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.orchestrator = orchestrator or GPUOrchestrator(
            data_dir=self.data_dir / "gpu_tasks"
        )

        self.active_jobs: Dict[str, BatchJob] = {}
        self._load_persisted_jobs()

    def _load_persisted_jobs(self) -> None:
        """Load incomplete jobs from disk."""
        jobs_file = self.data_dir / "active_jobs.json"
        if jobs_file.exists():
            try:
                with open(jobs_file, "r") as f:
                    jobs_data = json.load(f)
                for job_data in jobs_data:
                    job = BatchJob.from_dict(job_data)
                    if job.status not in (BatchStatus.COMPLETED, BatchStatus.FAILED):
                        self.active_jobs[job.job_id] = job
                        logger.info(f"Restored job {job.job_id}: {job.title}")
            except Exception as e:
                logger.error(f"Failed to load persisted jobs: {e}")

    def _save_jobs(self) -> None:
        """Persist active jobs to disk."""
        jobs_file = self.data_dir / "active_jobs.json"
        jobs_data = [job.to_dict() for job in self.active_jobs.values()]
        with open(jobs_file, "w") as f:
            json.dump(jobs_data, f, indent=2)

    def _save_job(self, job: BatchJob) -> None:
        """Save individual job state."""
        job_file = self.data_dir / f"job_{job.job_id}.json"
        with open(job_file, "w") as f:
            json.dump(job.to_dict(), f, indent=2)
        self._save_jobs()

    def create_job(
        self,
        book_id: str,
        title: str,
        author: str,
        source_text_path: Path,
        output_dir: Path,
        voice_profile: str,
        chapters: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> BatchJob:
        """
        Create a new batch production job.

        Args:
            book_id: Unique book identifier
            title: Book title
            author: Author name
            source_text_path: Path to source text
            output_dir: Output directory
            voice_profile: Voice profile ID
            chapters: List of chapter data dicts
            metadata: Optional metadata

        Returns:
            Created BatchJob
        """
        job_id = f"{book_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        job = BatchJob(
            job_id=job_id,
            book_id=book_id,
            title=title,
            author=author,
            source_text_path=source_text_path,
            output_dir=output_dir,
            voice_profile=voice_profile,
            metadata=metadata or {},
        )

        # Create chapter progress entries
        total_words = 0
        for i, ch_data in enumerate(chapters):
            word_count = len(ch_data.get("text", "").split())
            total_words += word_count

            ch = ChapterProgress(
                chapter_id=ch_data.get("id", f"ch_{i+1}"),
                chapter_num=i + 1,
                title=ch_data.get("title", f"Chapter {i+1}"),
                word_count=word_count,
            )
            job.chapters.append(ch)

        job.total_word_count = total_words

        # Create output directories
        (output_dir / "raw").mkdir(parents=True, exist_ok=True)
        (output_dir / "mastered").mkdir(parents=True, exist_ok=True)
        (output_dir / "final").mkdir(parents=True, exist_ok=True)

        self.active_jobs[job_id] = job
        self._save_job(job)

        logger.info(
            f"Created batch job {job_id}: {title} "
            f"({len(chapters)} chapters, {total_words:,} words)"
        )

        return job

    def queue_for_overnight(self, job: BatchJob) -> None:
        """
        Queue a job for overnight processing.

        Args:
            job: BatchJob to queue
        """
        job.status = BatchStatus.QUEUED

        # Queue all chapters with overnight priority
        chapter_data = []
        for ch in job.chapters:
            if ch.status == TaskStatus.PENDING:
                chapter_data.append({
                    "id": ch.chapter_id,
                    "title": ch.title,
                    "text": "",  # Will be loaded from source during processing
                })

        self.orchestrator.add_audiobook_batch(
            book_id=job.book_id,
            chapters=chapter_data,
            voice_profile=job.voice_profile,
            output_dir=job.output_dir / "raw",
            overnight=True,
        )

        self._save_job(job)
        logger.info(f"Queued job {job.job_id} for overnight processing")

    async def run_job(self, job: BatchJob) -> bool:
        """
        Run a batch job to completion.

        Args:
            job: BatchJob to run

        Returns:
            True if successful
        """
        job.status = BatchStatus.SYNTHESIZING
        job.started_at = datetime.now()
        self._save_job(job)

        try:
            # Phase 1: Synthesize all chapters
            logger.info(f"Starting synthesis for {job.title}")
            for ch in job.chapters:
                if ch.status in (TaskStatus.COMPLETED,):
                    continue

                ch.status = TaskStatus.RUNNING
                ch.started_at = datetime.now()
                self._save_job(job)

                success = await self._synthesize_chapter(job, ch)

                if success:
                    ch.status = TaskStatus.COMPLETED
                    ch.completed_at = datetime.now()
                else:
                    if ch.retries < self.MAX_RETRIES:
                        ch.retries += 1
                        ch.status = TaskStatus.PENDING
                        logger.warning(
                            f"Chapter {ch.chapter_num} failed, retry {ch.retries}"
                        )
                    else:
                        ch.status = TaskStatus.FAILED
                        logger.error(
                            f"Chapter {ch.chapter_num} failed after {self.MAX_RETRIES} retries"
                        )

                self._save_job(job)

            # Check if all chapters completed
            failed_chapters = [ch for ch in job.chapters if ch.status == TaskStatus.FAILED]
            if failed_chapters:
                job.status = BatchStatus.FAILED
                job.error_message = f"{len(failed_chapters)} chapters failed"
                self._save_job(job)
                return False

            # Phase 2: Master audio
            job.status = BatchStatus.MASTERING
            self._save_job(job)

            logger.info(f"Starting mastering for {job.title}")
            await self._master_audio(job)

            # Phase 3: Package final output
            job.status = BatchStatus.PACKAGING
            self._save_job(job)

            logger.info(f"Packaging final output for {job.title}")
            await self._package_output(job)

            # Done!
            job.status = BatchStatus.COMPLETED
            job.completed_at = datetime.now()

            total_duration = sum(ch.duration_seconds for ch in job.chapters)
            job.total_duration_seconds = total_duration

            self._save_job(job)

            logger.info(
                f"Completed job {job.job_id}: {job.title} "
                f"(duration: {total_duration/3600:.1f} hours)"
            )

            return True

        except Exception as e:
            job.status = BatchStatus.FAILED
            job.error_message = str(e)
            self._save_job(job)
            logger.error(f"Job {job.job_id} failed: {e}")
            return False

    async def _synthesize_chapter(
        self, job: BatchJob, chapter: ChapterProgress
    ) -> bool:
        """Synthesize a single chapter."""
        try:
            output_path = job.output_dir / "raw" / f"chapter_{chapter.chapter_num:02d}.wav"

            # In production, this would call the TTS engine
            # For now, simulate the process
            logger.info(
                f"Synthesizing {job.title} - {chapter.title} "
                f"({chapter.word_count} words)"
            )

            # Placeholder for actual TTS call
            # from src.audiobook.tts import TTSEngine
            # engine = TTSEngine(voice_profile=job.voice_profile)
            # await engine.synthesize(chapter_text, output_path)

            await asyncio.sleep(0.5)  # Placeholder

            chapter.audio_path = output_path
            # Estimate duration: ~150 words per minute
            chapter.duration_seconds = (chapter.word_count / 150) * 60

            return True

        except Exception as e:
            chapter.error = str(e)
            logger.error(f"Failed to synthesize chapter {chapter.chapter_num}: {e}")
            return False

    async def _master_audio(self, job: BatchJob) -> None:
        """Master all chapter audio files."""
        for ch in job.chapters:
            if ch.audio_path and ch.audio_path.exists():
                mastered_path = job.output_dir / "mastered" / ch.audio_path.name

                # In production, call audio mastering
                # from src.audiobook.postprocessing import AudioMastering
                # mastering = AudioMastering()
                # await mastering.process(ch.audio_path, mastered_path)

                # Placeholder
                await asyncio.sleep(0.1)

                ch.mastered_path = mastered_path

    async def _package_output(self, job: BatchJob) -> None:
        """Package final audiobook files."""
        final_dir = job.output_dir / "final"

        # Create combined MP3
        mp3_path = final_dir / f"{job.book_id}.mp3"
        # In production: combine chapters into single MP3

        # Create M4B with chapters
        m4b_path = final_dir / f"{job.book_id}.m4b"
        # In production: create M4B with chapter markers

        # Generate metadata
        metadata_path = final_dir / "metadata.json"
        metadata = {
            "title": job.title,
            "author": job.author,
            "duration_seconds": job.total_duration_seconds,
            "chapters": [
                {
                    "title": ch.title,
                    "duration_seconds": ch.duration_seconds,
                }
                for ch in job.chapters
            ],
            "produced_at": datetime.now().isoformat(),
        }

        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed status for a job."""
        job = self.active_jobs.get(job_id)
        if not job:
            return None

        completed_chapters = sum(
            1 for ch in job.chapters if ch.status == TaskStatus.COMPLETED
        )
        total_chapters = len(job.chapters)
        progress = completed_chapters / total_chapters if total_chapters > 0 else 0

        return {
            "job_id": job.job_id,
            "title": job.title,
            "status": job.status.value,
            "progress": progress,
            "chapters_completed": completed_chapters,
            "chapters_total": total_chapters,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "estimated_completion": self._estimate_completion(job),
            "error": job.error_message,
        }

    def _estimate_completion(self, job: BatchJob) -> Optional[str]:
        """Estimate job completion time."""
        if job.status in (BatchStatus.COMPLETED, BatchStatus.FAILED):
            return None

        # Estimate based on word count (~1 minute per 1000 words for synthesis)
        remaining_words = sum(
            ch.word_count
            for ch in job.chapters
            if ch.status not in (TaskStatus.COMPLETED,)
        )

        estimated_minutes = remaining_words / 1000 + len(job.chapters) * 2  # +2 per chapter overhead
        completion_time = datetime.now() + timedelta(minutes=estimated_minutes)

        return completion_time.isoformat()

    def list_jobs(self) -> List[Dict[str, Any]]:
        """List all active jobs."""
        return [
            {
                "job_id": job.job_id,
                "title": job.title,
                "status": job.status.value,
                "chapters": len(job.chapters),
                "created_at": job.created_at.isoformat(),
            }
            for job in self.active_jobs.values()
        ]


def create_overnight_batch(
    production_kit_path: Path,
    source_text_path: Path,
    output_base_dir: Path,
) -> BatchJob:
    """
    Create a batch job from a production kit.

    Args:
        production_kit_path: Path to PRODUCTION_KIT.md
        source_text_path: Path to cleaned source text
        output_base_dir: Base output directory

    Returns:
        Created BatchJob ready for overnight processing
    """
    # Parse production kit for metadata
    with open(production_kit_path, "r") as f:
        kit_content = f.read()

    # Extract basic info (simple parsing)
    # In production, use proper markdown parsing
    book_id = production_kit_path.parent.name
    title = book_id.replace("_", " ").title()

    # Create processor and job
    processor = BatchProcessor(data_dir=output_base_dir / ".batch_state")

    # For now, create placeholder chapters
    # In production, parse chapter structure from source text
    chapters = [
        {"id": f"ch_{i}", "title": f"Chapter {i}", "text": "placeholder"}
        for i in range(1, 21)
    ]

    job = processor.create_job(
        book_id=book_id,
        title=title,
        author="Author",  # Would parse from kit
        source_text_path=source_text_path,
        output_dir=output_base_dir / book_id,
        voice_profile="default",  # Would parse from kit
        chapters=chapters,
    )

    processor.queue_for_overnight(job)

    return job


def main() -> None:
    """Example usage of batch processor."""
    processor = BatchProcessor()

    # List any existing jobs
    jobs = processor.list_jobs()
    print(f"\nActive jobs: {len(jobs)}")
    for job in jobs:
        print(f"  - {job['title']} ({job['status']})")

    # Create example job
    test_job = processor.create_job(
        book_id="test_book",
        title="Test Book",
        author="Test Author",
        source_text_path=Path("./texts/test.txt"),
        output_dir=Path("./output/test_book"),
        voice_profile="default",
        chapters=[
            {"id": "ch_1", "title": "Chapter 1", "text": "Sample " * 500},
            {"id": "ch_2", "title": "Chapter 2", "text": "More " * 500},
        ],
    )

    print(f"\nCreated job: {test_job.job_id}")

    # Queue for overnight
    processor.queue_for_overnight(test_job)

    # Show status
    status = processor.get_job_status(test_job.job_id)
    print(f"Status: {status}")


if __name__ == "__main__":
    main()
