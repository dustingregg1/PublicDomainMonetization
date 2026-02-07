"""
Automation System for Public Domain Monetization

Leverages RTX 5080 GPU (16GB VRAM) for:
- Local TTS synthesis (Coqui XTTS-v2) - 6GB VRAM
- Local LLM inference (Ollama + Llama/Mistral) - 8GB VRAM
- Image generation (Stable Diffusion XL) - 10GB VRAM
- Overnight batch processing

Usage:
    # Queue overnight production
    python scripts/run_overnight.py --book all

    # Run queued jobs
    python scripts/run_overnight.py --run

    # Check status
    python scripts/run_overnight.py --status
"""

from .gpu_orchestrator import (
    GPUOrchestrator,
    GPUTask,
    GPUStats,
    TaskType,
    TaskPriority,
    TaskStatus,
)
from .batch_processor import (
    BatchProcessor,
    BatchJob,
    BatchStatus,
    ChapterProgress,
)

__all__ = [
    "GPUOrchestrator",
    "GPUTask",
    "GPUStats",
    "TaskType",
    "TaskPriority",
    "TaskStatus",
    "BatchProcessor",
    "BatchJob",
    "BatchStatus",
    "ChapterProgress",
]
