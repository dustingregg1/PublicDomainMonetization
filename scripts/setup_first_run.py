#!/usr/bin/env python3
"""
First-Run Setup Script

Run this once on a new machine to:
1. Install Python dependencies
2. Download XTTS-v2 model
3. Verify GPU access
4. Run a quick TTS smoke test

Usage:
    python scripts/setup_first_run.py           # Full setup
    python scripts/setup_first_run.py --skip-deps  # Skip pip install
    python scripts/setup_first_run.py --cpu-only    # Skip GPU checks
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def section(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def run(cmd: str, check: bool = True) -> subprocess.CompletedProcess:
    print(f"  $ {cmd}")
    return subprocess.run(cmd, shell=True, check=check)


def install_deps() -> bool:
    section("1. Installing Python dependencies")
    req_file = PROJECT_ROOT / "requirements.txt"
    result = run(f"pip install -r {req_file}", check=False)
    if result.returncode != 0:
        print("\n  WARNING: Some deps may have failed. Trying core packages...")
        run(
            "pip install torch torchvision torchaudio "
            "TTS pydub librosa soundfile diffusers transformers "
            "accelerate Pillow safetensors requests beautifulsoup4 lxml",
            check=False,
        )
    return True


def check_gpu() -> bool:
    section("2. Checking GPU availability")
    try:
        import torch

        print(f"  PyTorch: {torch.__version__}")
        print(f"  CUDA available: {torch.cuda.is_available()}")

        if torch.cuda.is_available():
            name = torch.cuda.get_device_name(0)
            vram = torch.cuda.get_device_properties(0).total_mem / 1024**3
            print(f"  GPU: {name}")
            print(f"  VRAM: {vram:.1f} GB")

            # Quick CUDA test
            t = torch.randn(1000, 1000, device="cuda")
            _ = t @ t.T
            print("  CUDA compute: OK")
            return True
        else:
            print("  No CUDA GPU detected - will use CPU (much slower)")
            return False
    except ImportError:
        print("  PyTorch not installed!")
        return False


def download_xtts_model() -> bool:
    section("3. Downloading XTTS-v2 model")

    model_dir = Path.home() / ".local" / "share" / "tts" / "tts_models--multilingual--multi-dataset--xtts_v2"
    if model_dir.exists() and (model_dir / "model.pth").exists():
        size_gb = sum(f.stat().st_size for f in model_dir.rglob("*") if f.is_file()) / 1024**3
        print(f"  Model already downloaded at {model_dir}")
        print(f"  Size: {size_gb:.1f} GB")
        return True

    print("  Downloading XTTS-v2 (this will take a few minutes)...")
    print("  You will need to accept the CPML license.")

    try:
        # Use TTS API to trigger download with license acceptance
        proc = subprocess.run(
            [
                sys.executable, "-c",
                "from TTS.api import TTS; "
                "tts = TTS(model_name='tts_models/multilingual/multi-dataset/xtts_v2', gpu=False); "
                "print('Model downloaded successfully')"
            ],
            input="y\n",
            text=True,
            capture_output=True,
            timeout=600,
        )
        if proc.returncode == 0:
            print("  Model downloaded successfully")
            return True
        else:
            print(f"  Download failed: {proc.stderr[-500:]}")
            return False
    except subprocess.TimeoutExpired:
        print("  Download timed out")
        return False
    except Exception as e:
        print(f"  Error: {e}")
        return False


def smoke_test_tts(use_gpu: bool) -> bool:
    section("4. TTS Smoke Test")
    try:
        from TTS.api import TTS

        device = "cuda" if use_gpu else "cpu"
        print(f"  Loading XTTS-v2 on {device}...")

        tts = TTS(
            model_name="tts_models/multilingual/multi-dataset/xtts_v2",
            gpu=use_gpu,
        )

        test_text = (
            "I am one of the Last Men. Two billion years have passed "
            "since your time."
        )
        output = PROJECT_ROOT / "output" / "test" / "smoke_test.wav"
        output.parent.mkdir(parents=True, exist_ok=True)

        print(f"  Synthesizing: '{test_text[:50]}...'")
        start = time.time()

        # Use default speaker if no reference audio
        tts.tts_to_file(
            text=test_text,
            file_path=str(output),
            language="en",
        )
        elapsed = time.time() - start

        if output.exists():
            size_kb = output.stat().st_size / 1024
            print(f"  Output: {output}")
            print(f"  Size: {size_kb:.0f} KB")
            print(f"  Time: {elapsed:.1f}s")
            print("  TTS smoke test PASSED")
            return True
        else:
            print("  FAILED: No output file")
            return False

    except Exception as e:
        print(f"  FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_source_text() -> bool:
    section("5. Verifying source text")
    text_file = PROJECT_ROOT / "texts" / "last_and_first_men_clean.txt"

    if text_file.exists():
        text = text_file.read_text(encoding="utf-8")
        words = len(text.split())
        print(f"  Source: {text_file}")
        print(f"  Words: {words:,}")

        sys.path.insert(0, str(PROJECT_ROOT))
        from src.sources.text_parser import TextParser

        parser = TextParser()
        chapters = parser.parse_file(text_file)
        print(f"  Chapters: {len(chapters)}")
        print(f"  Estimated audio: {words / 150 / 60:.1f} hours")
        return len(chapters) > 1
    else:
        print("  Source text not found!")
        print(f"  Expected: {text_file}")
        print("  Run: python scripts/test_pipeline.py --download")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="First-run setup for audiobook pipeline")
    parser.add_argument("--skip-deps", action="store_true", help="Skip pip install")
    parser.add_argument("--cpu-only", action="store_true", help="Don't require GPU")
    args = parser.parse_args()

    print("=" * 60)
    print("  Public Domain Audiobook Pipeline - First Run Setup")
    print("=" * 60)

    results = {}

    # 1. Dependencies
    if not args.skip_deps:
        results["deps"] = install_deps()
    else:
        print("\n  Skipping dependency install")

    # 2. GPU
    has_gpu = False
    if not args.cpu_only:
        has_gpu = check_gpu()
        results["gpu"] = has_gpu
    else:
        print("\n  Skipping GPU check (--cpu-only)")

    # 3. Model download
    results["model"] = download_xtts_model()

    # 4. Smoke test
    if results.get("model"):
        results["tts"] = smoke_test_tts(use_gpu=has_gpu)

    # 5. Source text
    results["source"] = verify_source_text()

    # Summary
    section("SETUP SUMMARY")
    for name, passed in results.items():
        status = "OK" if passed else "FAILED"
        print(f"  {name:12s} {status}")

    all_ok = all(results.values())
    if all_ok:
        print("\n  Setup complete! Ready for production.")
        print(f"\n  Next step:")
        print(f"    python scripts/run_overnight.py --book last_and_first_men")
    else:
        print("\n  Some checks failed. Fix the issues above and re-run.")
        sys.exit(1)


if __name__ == "__main__":
    main()
