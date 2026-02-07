#!/usr/bin/env python3
"""
Overnight Audiobook Production Script

Start this before bed, wake up to completed audiobooks.

Usage:
    python scripts/run_overnight.py --book maltese_falcon
    python scripts/run_overnight.py --book all --queue  # Queue all pending
    python scripts/run_overnight.py --status           # Check progress
    python scripts/run_overnight.py --resume           # Resume interrupted jobs

Designed for RTX 5080 with 16GB VRAM.
"""

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.automation.gpu_orchestrator import GPUOrchestrator, TaskPriority
from src.automation.batch_processor import BatchProcessor, BatchJob, BatchStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(project_root / "logs" / "overnight.log"),
    ],
)
logger = logging.getLogger("overnight")

# Book configurations
BOOK_CONFIGS = {
    "maltese_falcon": {
        "title": "The Maltese Falcon",
        "author": "Dashiell Hammett",
        "voice_profile": "hardboiled_detective",
        "production_kit": "kits/maltese_falcon/PRODUCTION_KIT.md",
        "source_text": "texts/maltese_falcon_clean.txt",
        "priority": 1,
    },
    "strong_poison": {
        "title": "Strong Poison",
        "author": "Dorothy L. Sayers",
        "voice_profile": "golden_age_british",
        "production_kit": "kits/strong_poison/PRODUCTION_KIT.md",
        "source_text": "texts/strong_poison_clean.txt",
        "priority": 3,
    },
    "last_and_first_men": {
        "title": "Last and First Men",
        "author": "Olaf Stapledon",
        "voice_profile": "philosophical_sf",
        "production_kit": "kits/last_and_first_men/PRODUCTION_KIT.md",
        "source_text": "texts/last_and_first_men_clean.txt",
        "priority": 2,  # FIRST in new launch order (lowest risk)
    },
}


def show_gpu_status() -> None:
    """Display current GPU status."""
    orchestrator = GPUOrchestrator()
    stats = orchestrator.get_gpu_stats()

    print("\n" + "=" * 50)
    print("GPU STATUS (RTX 5080)")
    print("=" * 50)
    print(f"Name:         {stats.name}")
    print(f"Memory:       {stats.memory_used_gb:.1f} / {stats.memory_total_gb:.1f} GB")
    print(f"Free:         {stats.memory_free_gb:.1f} GB")
    print(f"Utilization:  {stats.utilization_percent}%")
    print(f"Temperature:  {stats.temperature_celsius}C")
    print(f"Power Draw:   {stats.power_draw_watts}W")
    print("=" * 50)


def show_queue_status() -> None:
    """Display current queue and job status."""
    processor = BatchProcessor(data_dir=project_root / "batch_jobs")
    orchestrator = GPUOrchestrator(data_dir=project_root / "batch_jobs" / "gpu_tasks")

    # Show GPU status
    show_gpu_status()

    # Show queue status
    queue_status = orchestrator.get_queue_status()
    print("\nQUEUE STATUS")
    print("-" * 30)
    print(f"Pending tasks:   {queue_status['queue']['pending']}")
    print(f"Running tasks:   {queue_status['queue']['running']}")
    print(f"Completed tasks: {queue_status['queue']['completed']}")

    # Show estimate
    estimate = orchestrator.estimate_completion_time()
    print(f"\nEstimated completion: {estimate['estimated_completion']}")
    print(f"Time remaining: ~{estimate['total_estimated_minutes']:.0f} minutes")

    # Show batch jobs
    jobs = processor.list_jobs()
    if jobs:
        print("\nBATCH JOBS")
        print("-" * 30)
        for job in jobs:
            print(f"  {job['title']}: {job['status']} ({job['chapters']} chapters)")


def queue_book(book_id: str) -> None:
    """Queue a single book for overnight production."""
    if book_id not in BOOK_CONFIGS:
        print(f"Error: Unknown book '{book_id}'")
        print(f"Available: {', '.join(BOOK_CONFIGS.keys())}")
        return

    config = BOOK_CONFIGS[book_id]
    processor = BatchProcessor(data_dir=project_root / "batch_jobs")

    source_path = project_root / config["source_text"]
    output_dir = project_root / "output" / book_id

    # Check if source exists
    if not source_path.exists():
        print(f"Warning: Source text not found at {source_path}")
        print("Creating placeholder for pipeline testing...")
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_text(f"# {config['title']}\n\nPlaceholder text for testing.")

    # Generate chapter list (in production, parse from source)
    # For now, use standard chapter count
    chapter_counts = {
        "maltese_falcon": 20,
        "strong_poison": 16,
        "last_and_first_men": 16,
    }
    num_chapters = chapter_counts.get(book_id, 20)

    chapters = [
        {"id": f"ch_{i}", "title": f"Chapter {i}", "text": "placeholder"}
        for i in range(1, num_chapters + 1)
    ]

    # Create the job
    job = processor.create_job(
        book_id=book_id,
        title=config["title"],
        author=config["author"],
        source_text_path=source_path,
        output_dir=output_dir,
        voice_profile=config["voice_profile"],
        chapters=chapters,
        metadata={
            "production_kit": config["production_kit"],
            "queued_at": datetime.now().isoformat(),
        },
    )

    # Queue for overnight
    processor.queue_for_overnight(job)

    print(f"\nQueued: {config['title']}")
    print(f"Job ID: {job.job_id}")
    print(f"Chapters: {len(chapters)}")
    print(f"Output: {output_dir}")


def queue_all() -> None:
    """Queue all books in priority order."""
    # Sort by priority
    sorted_books = sorted(
        BOOK_CONFIGS.items(),
        key=lambda x: x[1]["priority"]
    )

    print("\nQueueing all books in priority order:")
    print("-" * 40)

    for book_id, config in sorted_books:
        print(f"\n{config['priority']}. {config['title']}")
        queue_book(book_id)


async def run_overnight() -> None:
    """Run overnight production on all queued jobs."""
    processor = BatchProcessor(data_dir=project_root / "batch_jobs")

    jobs = list(processor.active_jobs.values())
    pending_jobs = [j for j in jobs if j.status in (BatchStatus.QUEUED, BatchStatus.CREATED)]

    if not pending_jobs:
        print("No pending jobs to run.")
        return

    print(f"\nStarting overnight production of {len(pending_jobs)} jobs...")
    print("=" * 50)

    for job in pending_jobs:
        print(f"\nProcessing: {job.title}")
        print("-" * 30)

        success = await processor.run_job(job)

        if success:
            print(f"COMPLETED: {job.title}")
            print(f"  Duration: {job.total_duration_seconds/3600:.1f} hours")
            print(f"  Output: {job.output_dir}")
        else:
            print(f"FAILED: {job.title}")
            print(f"  Error: {job.error_message}")

    print("\n" + "=" * 50)
    print("OVERNIGHT PRODUCTION COMPLETE")
    print("=" * 50)


async def resume_jobs() -> None:
    """Resume any interrupted jobs."""
    processor = BatchProcessor(data_dir=project_root / "batch_jobs")

    jobs = list(processor.active_jobs.values())
    incomplete_jobs = [
        j for j in jobs
        if j.status not in (BatchStatus.COMPLETED, BatchStatus.FAILED)
    ]

    if not incomplete_jobs:
        print("No incomplete jobs to resume.")
        return

    print(f"\nResuming {len(incomplete_jobs)} incomplete jobs...")

    for job in incomplete_jobs:
        print(f"\nResuming: {job.title} (was {job.status.value})")
        success = await processor.run_job(job)
        print(f"Result: {'SUCCESS' if success else 'FAILED'}")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Overnight Audiobook Production",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_overnight.py --book maltese_falcon  # Queue single book
  python scripts/run_overnight.py --book all             # Queue all books
  python scripts/run_overnight.py --run                  # Run queued jobs
  python scripts/run_overnight.py --status               # Check status
  python scripts/run_overnight.py --resume               # Resume interrupted
        """,
    )

    parser.add_argument(
        "--book",
        help="Book ID to queue (maltese_falcon, strong_poison, last_and_first_men, or 'all')",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Run overnight production on queued jobs",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show current GPU and queue status",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume interrupted jobs",
    )
    parser.add_argument(
        "--gpu",
        action="store_true",
        help="Show GPU status only",
    )

    args = parser.parse_args()

    # Create logs directory
    (project_root / "logs").mkdir(exist_ok=True)

    if args.gpu:
        show_gpu_status()
    elif args.status:
        show_queue_status()
    elif args.book:
        if args.book == "all":
            queue_all()
        else:
            queue_book(args.book)
    elif args.run:
        asyncio.run(run_overnight())
    elif args.resume:
        asyncio.run(resume_jobs())
    else:
        parser.print_help()
        print("\nQuick start:")
        print("  1. Queue books:  python scripts/run_overnight.py --book all")
        print("  2. Start run:    python scripts/run_overnight.py --run")
        print("  3. Go to sleep!")


if __name__ == "__main__":
    main()
