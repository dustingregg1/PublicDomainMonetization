"""
GPU Orchestrator for RTX 5080

Manages GPU resources for parallel/sequential processing of:
- TTS synthesis
- LLM inference
- Image generation
- Audio processing

Designed for overnight batch processing with monitoring.
"""

import os
import json
import logging
import asyncio
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from concurrent.futures import ThreadPoolExecutor
import threading

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task priority levels."""
    CRITICAL = 1  # Must complete ASAP
    HIGH = 2      # Important, run soon
    NORMAL = 3    # Standard processing
    LOW = 4       # Background, when idle
    OVERNIGHT = 5 # Batch overnight only


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(Enum):
    """Types of GPU tasks."""
    TTS_SYNTHESIS = "tts"
    LLM_INFERENCE = "llm"
    IMAGE_GENERATION = "image"
    AUDIO_MASTERING = "audio"
    VIDEO_GENERATION = "video"
    BATCH_MIXED = "batch"


@dataclass
class GPUTask:
    """A GPU-accelerated task."""
    task_id: str
    task_type: TaskType
    priority: TaskPriority
    input_data: Dict[str, Any]
    output_path: Path
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_duration_minutes: int = 0
    actual_duration_minutes: int = 0
    gpu_memory_required_gb: float = 0.0
    callback: Optional[Callable] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "progress": self.progress,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "estimated_duration_minutes": self.estimated_duration_minutes,
            "actual_duration_minutes": self.actual_duration_minutes,
        }


@dataclass
class GPUStats:
    """GPU statistics."""
    name: str = "Unknown"
    memory_total_gb: float = 0.0
    memory_used_gb: float = 0.0
    memory_free_gb: float = 0.0
    utilization_percent: float = 0.0
    temperature_celsius: float = 0.0
    power_draw_watts: float = 0.0


class GPUOrchestrator:
    """
    Orchestrates GPU workloads for the RTX 5080.

    Features:
    - Task queue with priority scheduling
    - GPU memory management
    - Overnight batch processing mode
    - Progress monitoring and logging
    - Automatic error recovery
    - Power/thermal throttling awareness
    """

    # RTX 5080 specifications
    RTX_5080_VRAM_GB = 16.0
    RTX_5080_TDP_WATTS = 320

    # Task VRAM requirements (conservative estimates)
    VRAM_REQUIREMENTS = {
        TaskType.TTS_SYNTHESIS: 6.0,      # Coqui XTTS-v2
        TaskType.LLM_INFERENCE: 8.0,      # 7B model quantized
        TaskType.IMAGE_GENERATION: 10.0,  # SDXL
        TaskType.AUDIO_MASTERING: 2.0,    # Light GPU use
        TaskType.VIDEO_GENERATION: 12.0,  # Heavy
        TaskType.BATCH_MIXED: 8.0,        # Average
    }

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        max_concurrent_tasks: int = 1,  # GPU tasks usually sequential
        overnight_start_hour: int = 23,
        overnight_end_hour: int = 6,
    ) -> None:
        """
        Initialize GPU orchestrator.

        Args:
            data_dir: Directory for task data and logs
            max_concurrent_tasks: Maximum parallel GPU tasks
            overnight_start_hour: Hour to start overnight batch (24h)
            overnight_end_hour: Hour to end overnight batch (24h)
        """
        self.data_dir = data_dir or Path.cwd() / "gpu_tasks"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.max_concurrent = max_concurrent_tasks
        self.overnight_start = overnight_start_hour
        self.overnight_end = overnight_end_hour

        self.task_queue: List[GPUTask] = []
        self.running_tasks: Dict[str, GPUTask] = {}
        self.completed_tasks: List[GPUTask] = []

        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=max_concurrent_tasks)
        self._running = False
        self._overnight_mode = False

        self._load_state()

    def _load_state(self) -> None:
        """Load persisted task queue state."""
        state_file = self.data_dir / "orchestrator_state.json"
        if state_file.exists():
            try:
                with open(state_file, "r") as f:
                    state = json.load(f)
                    logger.info(f"Loaded {len(state.get('pending_tasks', []))} pending tasks")
            except Exception as e:
                logger.warning(f"Could not load state: {e}")

    def _save_state(self) -> None:
        """Persist task queue state."""
        state_file = self.data_dir / "orchestrator_state.json"
        state = {
            "pending_tasks": [t.to_dict() for t in self.task_queue],
            "completed_count": len(self.completed_tasks),
            "saved_at": datetime.now().isoformat(),
        }
        with open(state_file, "w") as f:
            json.dump(state, f, indent=2)

    def get_gpu_stats(self) -> GPUStats:
        """
        Get current GPU statistics using nvidia-smi.

        Returns:
            GPUStats with current GPU state
        """
        stats = GPUStats()

        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu,power.draw",
                    "--format=csv,noheader,nounits"
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                parts = result.stdout.strip().split(", ")
                if len(parts) >= 7:
                    stats.name = parts[0]
                    stats.memory_total_gb = float(parts[1]) / 1024
                    stats.memory_used_gb = float(parts[2]) / 1024
                    stats.memory_free_gb = float(parts[3]) / 1024
                    stats.utilization_percent = float(parts[4])
                    stats.temperature_celsius = float(parts[5])
                    stats.power_draw_watts = float(parts[6])

        except Exception as e:
            logger.warning(f"Could not get GPU stats: {e}")
            # Return defaults for RTX 5080
            stats.name = "NVIDIA GeForce RTX 5080 (estimated)"
            stats.memory_total_gb = self.RTX_5080_VRAM_GB
            stats.memory_free_gb = self.RTX_5080_VRAM_GB

        return stats

    def can_run_task(self, task: GPUTask) -> tuple[bool, str]:
        """
        Check if a task can run given current GPU state.

        Args:
            task: Task to check

        Returns:
            Tuple of (can_run, reason)
        """
        stats = self.get_gpu_stats()

        # Check VRAM
        required_vram = self.VRAM_REQUIREMENTS.get(task.task_type, 8.0)
        if stats.memory_free_gb < required_vram:
            return False, f"Insufficient VRAM: {stats.memory_free_gb:.1f}GB free, {required_vram:.1f}GB needed"

        # Check temperature (throttle at 80C)
        if stats.temperature_celsius > 80:
            return False, f"GPU too hot: {stats.temperature_celsius}C"

        # Check overnight mode
        current_hour = datetime.now().hour
        is_overnight = (
            current_hour >= self.overnight_start or
            current_hour < self.overnight_end
        )

        if task.priority == TaskPriority.OVERNIGHT and not is_overnight:
            return False, "Task scheduled for overnight only"

        # Check concurrent limit
        if len(self.running_tasks) >= self.max_concurrent:
            return False, f"Max concurrent tasks ({self.max_concurrent}) reached"

        return True, "OK"

    def add_task(
        self,
        task_type: TaskType,
        input_data: Dict[str, Any],
        output_path: Path,
        priority: TaskPriority = TaskPriority.NORMAL,
        estimated_minutes: int = 30,
        callback: Optional[Callable] = None,
    ) -> GPUTask:
        """
        Add a task to the queue.

        Args:
            task_type: Type of GPU task
            input_data: Task input parameters
            output_path: Where to save output
            priority: Task priority
            estimated_minutes: Estimated duration
            callback: Optional completion callback

        Returns:
            Created GPUTask
        """
        task_id = f"{task_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        task = GPUTask(
            task_id=task_id,
            task_type=task_type,
            priority=priority,
            input_data=input_data,
            output_path=output_path,
            estimated_duration_minutes=estimated_minutes,
            gpu_memory_required_gb=self.VRAM_REQUIREMENTS.get(task_type, 8.0),
            callback=callback,
        )

        with self._lock:
            self.task_queue.append(task)
            # Sort by priority
            self.task_queue.sort(key=lambda t: t.priority.value)

        self._save_state()
        logger.info(f"Added task {task_id} (priority: {priority.name})")

        return task

    def add_audiobook_batch(
        self,
        book_id: str,
        chapters: List[Dict[str, Any]],
        voice_profile: str,
        output_dir: Path,
        overnight: bool = True,
    ) -> List[GPUTask]:
        """
        Add a batch of audiobook chapter synthesis tasks.

        Args:
            book_id: Book identifier
            chapters: List of chapter data
            voice_profile: Voice profile ID
            output_dir: Output directory
            overnight: Schedule for overnight processing

        Returns:
            List of created tasks
        """
        tasks = []
        priority = TaskPriority.OVERNIGHT if overnight else TaskPriority.NORMAL

        for i, chapter in enumerate(chapters):
            task = self.add_task(
                task_type=TaskType.TTS_SYNTHESIS,
                input_data={
                    "book_id": book_id,
                    "chapter_index": i,
                    "chapter_id": chapter.get("id", f"chapter_{i+1}"),
                    "chapter_title": chapter.get("title", f"Chapter {i+1}"),
                    "text": chapter.get("text", ""),
                    "voice_profile": voice_profile,
                },
                output_path=output_dir / f"chapter_{i+1:02d}.wav",
                priority=priority,
                estimated_minutes=len(chapter.get("text", "")) // 1000 + 5,  # ~1min per 1000 chars
            )
            tasks.append(task)

        logger.info(f"Queued {len(tasks)} chapters for {book_id}")
        return tasks

    def add_cover_art_batch(
        self,
        book_id: str,
        prompts: List[str],
        output_dir: Path,
        dimensions: tuple[int, int] = (3000, 3000),
    ) -> List[GPUTask]:
        """
        Add batch of cover art generation tasks.

        Args:
            book_id: Book identifier
            prompts: List of prompts for different variations
            output_dir: Output directory
            dimensions: Output image dimensions

        Returns:
            List of created tasks
        """
        tasks = []

        for i, prompt in enumerate(prompts):
            task = self.add_task(
                task_type=TaskType.IMAGE_GENERATION,
                input_data={
                    "book_id": book_id,
                    "prompt": prompt,
                    "negative_prompt": self._get_negative_prompt(book_id),
                    "width": dimensions[0],
                    "height": dimensions[1],
                    "variation": i,
                },
                output_path=output_dir / f"cover_v{i+1}.png",
                priority=TaskPriority.NORMAL,
                estimated_minutes=2,
            )
            tasks.append(task)

        return tasks

    def _get_negative_prompt(self, book_id: str) -> str:
        """Get negative prompt for cover art based on book."""
        # Avoid trade dress issues
        negatives = {
            "maltese_falcon": (
                "film noir lighting, 1940s aesthetic, fedora shadows, "
                "Humphrey Bogart style, Warner Bros movie poster style, "
                "black and white photography, movie still, film scene"
            ),
            "murder_vicarage": (
                "yellow book spine, Agatha Christie logo, signature font, "
                "modern Christie cover style, TV adaptation imagery"
            ),
            "strong_poison": (
                "yellow book spine, Hodder Stoughton style, "
                "TV adaptation imagery, Ian Carmichael"
            ),
        }

        base_negative = (
            "low quality, blurry, text, watermark, logo, "
            "photograph, photorealistic face, celebrity likeness"
        )

        specific = negatives.get(book_id, "")
        return f"{base_negative}, {specific}" if specific else base_negative

    async def run_task(self, task: GPUTask) -> bool:
        """
        Execute a single GPU task.

        Args:
            task: Task to execute

        Returns:
            True if successful
        """
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()

        try:
            logger.info(f"Starting task {task.task_id}")

            if task.task_type == TaskType.TTS_SYNTHESIS:
                await self._run_tts_task(task)
            elif task.task_type == TaskType.IMAGE_GENERATION:
                await self._run_image_task(task)
            elif task.task_type == TaskType.LLM_INFERENCE:
                await self._run_llm_task(task)
            elif task.task_type == TaskType.AUDIO_MASTERING:
                await self._run_mastering_task(task)
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")

            task.status = TaskStatus.COMPLETED
            task.progress = 1.0
            task.completed_at = datetime.now()
            task.actual_duration_minutes = int(
                (task.completed_at - task.started_at).total_seconds() / 60
            )

            logger.info(
                f"Completed task {task.task_id} in {task.actual_duration_minutes} minutes"
            )

            if task.callback:
                task.callback(task)

            return True

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.now()
            logger.error(f"Task {task.task_id} failed: {e}")
            return False

    async def _run_tts_task(self, task: GPUTask) -> None:
        """Run TTS synthesis task."""
        # This would integrate with the audiobook pipeline
        # For now, placeholder that shows the structure

        data = task.input_data
        logger.info(
            f"TTS: {data['book_id']} - {data['chapter_title']} "
            f"({len(data['text'])} chars)"
        )

        # Simulate TTS processing
        # In production, this calls src.audiobook.tts.tts_engine
        task.progress = 0.5
        await asyncio.sleep(1)  # Placeholder
        task.progress = 1.0

    async def _run_image_task(self, task: GPUTask) -> None:
        """Run image generation task."""
        data = task.input_data
        logger.info(
            f"Image: {data['book_id']} variation {data['variation']} "
            f"({data['width']}x{data['height']})"
        )

        # Would call Stable Diffusion
        task.progress = 0.5
        await asyncio.sleep(1)  # Placeholder
        task.progress = 1.0

    async def _run_llm_task(self, task: GPUTask) -> None:
        """Run LLM inference task."""
        data = task.input_data
        logger.info(f"LLM: {data.get('task_name', 'inference')}")

        # Would call Ollama or local LLM
        task.progress = 0.5
        await asyncio.sleep(1)  # Placeholder
        task.progress = 1.0

    async def _run_mastering_task(self, task: GPUTask) -> None:
        """Run audio mastering task."""
        data = task.input_data
        logger.info(f"Mastering: {data.get('book_id', 'unknown')}")

        # Would call src.audiobook.postprocessing.audio_mastering
        task.progress = 0.5
        await asyncio.sleep(1)  # Placeholder
        task.progress = 1.0

    async def process_queue(self) -> None:
        """Process tasks in the queue."""
        self._running = True

        while self._running and self.task_queue:
            # Get next task
            with self._lock:
                if not self.task_queue:
                    break

                task = None
                for t in self.task_queue:
                    can_run, reason = self.can_run_task(t)
                    if can_run:
                        task = t
                        self.task_queue.remove(t)
                        self.running_tasks[t.task_id] = t
                        break

                if not task:
                    # No runnable tasks, wait
                    await asyncio.sleep(60)
                    continue

            # Run the task
            success = await self.run_task(task)

            # Move to completed
            with self._lock:
                del self.running_tasks[task.task_id]
                self.completed_tasks.append(task)

            self._save_state()

        self._running = False

    def start_overnight_batch(self) -> None:
        """Start overnight batch processing."""
        logger.info("Starting overnight batch processing")
        self._overnight_mode = True

        # Run async processing
        asyncio.run(self.process_queue())

    def stop_processing(self) -> None:
        """Stop processing (gracefully finish current task)."""
        logger.info("Stopping processing after current task")
        self._running = False

    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status."""
        stats = self.get_gpu_stats()

        return {
            "gpu": {
                "name": stats.name,
                "memory_used_gb": round(stats.memory_used_gb, 1),
                "memory_free_gb": round(stats.memory_free_gb, 1),
                "utilization_percent": stats.utilization_percent,
                "temperature_celsius": stats.temperature_celsius,
            },
            "queue": {
                "pending": len(self.task_queue),
                "running": len(self.running_tasks),
                "completed": len(self.completed_tasks),
            },
            "tasks": {
                "pending": [t.to_dict() for t in self.task_queue[:10]],
                "running": [t.to_dict() for t in self.running_tasks.values()],
            },
            "overnight_mode": self._overnight_mode,
            "is_running": self._running,
        }

    def estimate_completion_time(self) -> Dict[str, Any]:
        """Estimate when queue will complete."""
        total_minutes = sum(t.estimated_duration_minutes for t in self.task_queue)

        # Add running task remaining time
        for task in self.running_tasks.values():
            remaining = task.estimated_duration_minutes * (1 - task.progress)
            total_minutes += remaining

        completion_time = datetime.now() + timedelta(minutes=total_minutes)

        return {
            "total_estimated_minutes": total_minutes,
            "estimated_completion": completion_time.isoformat(),
            "tasks_remaining": len(self.task_queue) + len(self.running_tasks),
        }


def main() -> None:
    """Example usage of GPU orchestrator."""
    orchestrator = GPUOrchestrator()

    # Show GPU stats
    stats = orchestrator.get_gpu_stats()
    print(f"\nGPU: {stats.name}")
    print(f"Memory: {stats.memory_used_gb:.1f}/{stats.memory_total_gb:.1f} GB")
    print(f"Temperature: {stats.temperature_celsius}C")

    # Queue some tasks
    orchestrator.add_audiobook_batch(
        book_id="maltese_falcon_2026",
        chapters=[
            {"id": "ch1", "title": "Chapter 1", "text": "Sample text " * 500},
            {"id": "ch2", "title": "Chapter 2", "text": "More text " * 500},
        ],
        voice_profile="hardboiled_detective",
        output_dir=Path("./output/maltese_falcon/raw"),
        overnight=True,
    )

    # Show queue status
    status = orchestrator.get_queue_status()
    print(f"\nQueue: {status['queue']['pending']} pending tasks")

    # Estimate completion
    estimate = orchestrator.estimate_completion_time()
    print(f"Estimated completion: {estimate['estimated_completion']}")


if __name__ == "__main__":
    main()
