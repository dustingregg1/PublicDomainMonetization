#!/usr/bin/env python3
"""
Overnight Audiobook Production Script

Start this before bed, wake up to completed audiobooks.

Usage:
    python scripts/run_overnight.py --download last_and_first_men  # Get source text
    python scripts/run_overnight.py --book last_and_first_men      # Queue single book
    python scripts/run_overnight.py --book all                     # Queue all books
    python scripts/run_overnight.py --run                          # Run queued jobs
    python scripts/run_overnight.py --status                       # Check progress
    python scripts/run_overnight.py --resume                       # Resume interrupted

Designed for RTX 5080 with 16GB VRAM.
"""

import argparse
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.automation.gpu_orchestrator import GPUOrchestrator
from src.automation.batch_processor import BatchProcessor, BatchStatus
from src.sources.gutenberg import GutenbergSource
from src.sources.text_parser import TextParser

# Configure logging
log_dir = project_root / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_dir / "overnight.log"),
    ],
)
logger = logging.getLogger("overnight")

# Book configurations with full metadata
BOOK_CONFIGS = {
    "last_and_first_men": {
        "title": "Last and First Men",
        "author": "Olaf Stapledon",
        "voice_profile": "philosophical_sf",
        "production_kit": "kits/last_and_first_men/PRODUCTION_KIT.md",
        "source_text": "texts/last_and_first_men_clean.txt",
        "gutenberg_id": 17662,
        "priority": 1,  # FIRST in launch order (lowest risk, global PD)
        "mastering_profile": "audiobook_dense",
        "genre": "Science Fiction",
        "description": (
            "A telepathic message from two billion years in the future tells "
            "the complete history of humanity - from our present day through "
            "eighteen distinct human species."
        ),
        "disclaimer": (
            "This is an independent publication based on the original 1930 "
            "public domain text by Olaf Stapledon. This work is not authorized, "
            "sponsored, or endorsed by any estate or affiliated party."
        ),
    },
    "maltese_falcon": {
        "title": "The Maltese Falcon",
        "author": "Dashiell Hammett",
        "voice_profile": "hardboiled_detective",
        "production_kit": "kits/maltese_falcon/PRODUCTION_KIT.md",
        "source_text": "texts/maltese_falcon_clean.txt",
        "gutenberg_id": None,  # Not on Gutenberg - provide manually
        "priority": 2,
        "mastering_profile": "audiobook_dramatic",
        "genre": "Mystery",
        "description": "The classic hardboiled detective novel.",
        "disclaimer": (
            "This is an independent publication based on the original 1930 "
            "public domain text by Dashiell Hammett. This work is not authorized, "
            "sponsored, or endorsed by any estate or affiliated party."
        ),
    },
    "strong_poison": {
        "title": "Strong Poison",
        "author": "Dorothy L. Sayers",
        "voice_profile": "golden_age_british",
        "production_kit": "kits/strong_poison/PRODUCTION_KIT.md",
        "source_text": "texts/strong_poison_clean.txt",
        "gutenberg_id": None,  # Not on Gutenberg - provide manually
        "priority": 3,
        "mastering_profile": "audiobook_standard",
        "genre": "Mystery",
        "description": "A golden age British mystery.",
        "disclaimer": (
            "This is an independent publication based on the original 1930 "
            "public domain text by Dorothy L. Sayers. This work is not authorized, "
            "sponsored, or endorsed by any estate or affiliated party."
        ),
    },
}


def show_gpu_status() -> None:
    """Display current GPU status."""
    orchestrator = GPUOrchestrator()
    stats = orchestrator.get_gpu_stats()

    print("\n" + "=" * 50)
    print("GPU STATUS")
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

    show_gpu_status()

    queue_status = orchestrator.get_queue_status()
    print("\nQUEUE STATUS")
    print("-" * 30)
    print(f"Pending tasks:   {queue_status['queue']['pending']}")
    print(f"Running tasks:   {queue_status['queue']['running']}")
    print(f"Completed tasks: {queue_status['queue']['completed']}")

    estimate = orchestrator.estimate_completion_time()
    print(f"\nEstimated completion: {estimate['estimated_completion']}")
    print(f"Time remaining: ~{estimate['total_estimated_minutes']:.0f} minutes")

    jobs = processor.list_jobs()
    if jobs:
        print("\nBATCH JOBS")
        print("-" * 30)
        for job in jobs:
            print(f"  {job['title']}: {job['status']} ({job['chapters']} chapters)")


def download_source(book_id: str) -> Path:
    """Download and clean source text for a book."""
    config = BOOK_CONFIGS.get(book_id)
    if not config:
        print(f"Error: Unknown book '{book_id}'")
        print(f"Available: {', '.join(BOOK_CONFIGS.keys())}")
        sys.exit(1)

    gutenberg_id = config.get("gutenberg_id")
    if gutenberg_id is None:
        print(f"'{book_id}' is not available on Project Gutenberg.")
        print(f"Provide the source text manually at:")
        print(f"  {project_root / config['source_text']}")
        sys.exit(1)

    source = GutenbergSource(cache_dir=project_root / "texts" / ".gutenberg_cache")
    output_path = project_root / config["source_text"]

    print(f"\nDownloading: {config['title']}")
    print(f"  Gutenberg ID: {gutenberg_id}")
    print(f"  Output: {output_path}")

    path = source.download_and_clean(gutenberg_id, output_path)

    # Parse and show chapter summary
    parser = TextParser()
    chapters = parser.parse_file(path)
    print(f"\n{parser.get_chapter_summary(chapters)}")

    return path


def queue_book(book_id: str) -> None:
    """Queue a single book for overnight production."""
    if book_id not in BOOK_CONFIGS:
        print(f"Error: Unknown book '{book_id}'")
        print(f"Available: {', '.join(BOOK_CONFIGS.keys())}")
        return

    config = BOOK_CONFIGS[book_id]
    source_path = project_root / config["source_text"]

    # Check if source exists, download if possible
    if not source_path.exists():
        if config.get("gutenberg_id"):
            print("Source text not found. Downloading from Project Gutenberg...")
            download_source(book_id)
        else:
            print(f"Error: Source text not found at {source_path}")
            print(f"'{book_id}' must be provided manually (not on Gutenberg).")
            return

    # Parse chapters from source text
    parser = TextParser()
    parsed_chapters = parser.parse_file(source_path)

    print(f"\n{parser.get_chapter_summary(parsed_chapters)}")

    # Create batch job with real chapter data
    processor = BatchProcessor(data_dir=project_root / "batch_jobs")
    output_dir = project_root / "output" / book_id

    chapters_data = [
        {
            "id": ch.chapter_id,
            "title": ch.title,
            "text": ch.text,
        }
        for ch in parsed_chapters
    ]

    # Store chapter texts in metadata for the batch processor to use
    parsed_texts = {ch.chapter_id: ch.text for ch in parsed_chapters}

    job = processor.create_job(
        book_id=book_id,
        title=config["title"],
        author=config["author"],
        source_text_path=source_path,
        output_dir=output_dir,
        voice_profile=config["voice_profile"],
        chapters=chapters_data,
        metadata={
            "production_kit": config["production_kit"],
            "queued_at": datetime.now().isoformat(),
            "parsed_chapters": parsed_texts,
            "mastering_profile": config.get("mastering_profile", "audiobook_standard"),
            "genre": config.get("genre", "Fiction"),
            "description": config.get("description", ""),
            "disclaimer": config.get("disclaimer", ""),
        },
    )

    processor.queue_for_overnight(job)

    total_words = sum(c.word_count for c in parsed_chapters)
    print(f"\nQueued: {config['title']}")
    print(f"Job ID: {job.job_id}")
    print(f"Chapters: {len(parsed_chapters)}")
    print(f"Total words: {total_words:,}")
    print(f"Est. audio: {total_words / 150 / 60:.1f} hours")
    print(f"Output: {output_dir}")


def queue_all() -> None:
    """Queue all books in priority order."""
    sorted_books = sorted(
        BOOK_CONFIGS.items(),
        key=lambda x: x[1]["priority"]
    )

    print("\nQueueing all books in priority order:")
    print("-" * 40)

    for book_id, config in sorted_books:
        source_path = project_root / config["source_text"]
        if source_path.exists() or config.get("gutenberg_id"):
            print(f"\n{config['priority']}. {config['title']}")
            queue_book(book_id)
        else:
            print(f"\n{config['priority']}. {config['title']} - SKIPPED (no source text)")


async def run_overnight() -> None:
    """Run overnight production on all queued jobs."""
    processor = BatchProcessor(data_dir=project_root / "batch_jobs")

    jobs = list(processor.active_jobs.values())
    pending_jobs = [j for j in jobs if j.status in (BatchStatus.QUEUED, BatchStatus.CREATED)]

    if not pending_jobs:
        print("No pending jobs to run.")
        print("Queue a book first: python scripts/run_overnight.py --book last_and_first_men")
        return

    print(f"\nStarting overnight production of {len(pending_jobs)} jobs...")
    print("=" * 50)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    for job in pending_jobs:
        print(f"\nProcessing: {job.title}")
        print(f"  Chapters: {len(job.chapters)}")
        print(f"  Words: {job.total_word_count:,}")
        print("-" * 30)

        success = await processor.run_job(job)

        if success:
            print(f"\nCOMPLETED: {job.title}")
            print(f"  Duration: {job.total_duration_seconds/3600:.1f} hours of audio")
            print(f"  Output: {job.output_dir}")
        else:
            print(f"\nFAILED: {job.title}")
            print(f"  Error: {job.error_message}")

    print("\n" + "=" * 50)
    print("OVERNIGHT PRODUCTION COMPLETE")
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
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
  python scripts/run_overnight.py --download last_and_first_men  # Get source text
  python scripts/run_overnight.py --book last_and_first_men      # Queue single book
  python scripts/run_overnight.py --book all                     # Queue all books
  python scripts/run_overnight.py --run                          # Run queued jobs
  python scripts/run_overnight.py --status                       # Check status
  python scripts/run_overnight.py --resume                       # Resume interrupted

Full pipeline:
  python scripts/run_overnight.py --download last_and_first_men
  python scripts/run_overnight.py --book last_and_first_men
  python scripts/run_overnight.py --run
        """,
    )

    parser.add_argument(
        "--book",
        help="Book ID to queue (last_and_first_men, maltese_falcon, strong_poison, or 'all')",
    )
    parser.add_argument(
        "--download",
        help="Download source text from Project Gutenberg (e.g., last_and_first_men)",
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

    if args.gpu:
        show_gpu_status()
    elif args.status:
        show_queue_status()
    elif args.download:
        download_source(args.download)
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
        print("\n" + "=" * 50)
        print("QUICK START (Last and First Men):")
        print("=" * 50)
        print("  1. Download:  python scripts/run_overnight.py --download last_and_first_men")
        print("  2. Queue:     python scripts/run_overnight.py --book last_and_first_men")
        print("  3. Run:       python scripts/run_overnight.py --run")
        print("  4. Go to sleep!")


if __name__ == "__main__":
    main()
