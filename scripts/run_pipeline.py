#!/usr/bin/env python3
"""
Quick Pipeline Runner
====================

Simplified interface for running the PD monetization pipeline.

Usage:
    python run_pipeline.py                    # Status check
    python run_pipeline.py maltese           # Full pipeline for Maltese Falcon
    python run_pipeline.py strong            # Full pipeline for Strong Poison
    python run_pipeline.py last              # Full pipeline for Last and First Men
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from orchestration.master_orchestrator import PDMonetizationOrchestrator

# Title shortcuts
SHORTCUTS = {
    "maltese": "The Maltese Falcon",
    "strong": "Strong Poison",
    "last": "Last and First Men",
    "cimarron": "Cimarron",
    "42nd": "The 42nd Parallel",
}


def main():
    orchestrator = PDMonetizationOrchestrator(
        project_root=Path(__file__).parent.parent
    )

    if len(sys.argv) < 2:
        # Show status
        orchestrator.cli_status()
        print("\nQuick commands:")
        for shortcut, title in SHORTCUTS.items():
            print(f"  python run_pipeline.py {shortcut}  →  {title}")
        return

    # Get title from shortcut or use as-is
    arg = sys.argv[1].lower()
    title = SHORTCUTS.get(arg, " ".join(sys.argv[1:]))

    # Run full pipeline
    print(f"\nRunning full pipeline for: {title}")
    result = orchestrator.run_full_pipeline(title)

    if result["success"]:
        print("\n" + "="*60)
        print("SUCCESS!")
        print("="*60)
        print(f"\nKit generated at: {result['results'].get('kit_path', 'N/A')}")
    else:
        print(f"\nPipeline failed: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()
