#!/usr/bin/env python3
"""
Pipeline Validation Script

Tests each stage of the audiobook production pipeline independently.
Use this to verify your setup before running overnight production.

Usage:
    python scripts/test_pipeline.py --all              # Run all tests
    python scripts/test_pipeline.py --download          # Test Gutenberg download
    python scripts/test_pipeline.py --parse             # Test chapter parsing
    python scripts/test_pipeline.py --tts               # Test TTS (requires GPU)
    python scripts/test_pipeline.py --master            # Test audio mastering
    python scripts/test_pipeline.py --package           # Test packaging
    python scripts/test_pipeline.py --cover             # Test cover art (requires GPU)
    python scripts/test_pipeline.py --gpu               # Test GPU availability
"""

import argparse
import logging
import sys
import time
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("test_pipeline")


def test_gpu() -> bool:
    """Test GPU availability and CUDA support."""
    print("\n" + "=" * 50)
    print("TEST: GPU Availability")
    print("=" * 50)

    try:
        import torch
        print(f"PyTorch version: {torch.__version__}")
        print(f"CUDA available: {torch.cuda.is_available()}")

        if torch.cuda.is_available():
            print(f"CUDA version: {torch.version.cuda}")
            print(f"GPU: {torch.cuda.get_device_name(0)}")
            props = torch.cuda.get_device_properties(0)
            vram = getattr(props, "total_memory", getattr(props, "total_mem", 0))
            print(f"VRAM: {vram / 1e9:.1f} GB")
            print("PASS")
            return True
        else:
            print("WARNING: No CUDA GPU detected. TTS will use CPU (much slower).")
            return True  # Not a failure, just slow

    except ImportError:
        print("FAIL: PyTorch not installed")
        print("  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121")
        return False


def test_download() -> bool:
    """Test downloading from Project Gutenberg."""
    print("\n" + "=" * 50)
    print("TEST: Gutenberg Download")
    print("=" * 50)

    try:
        from src.sources.gutenberg import GutenbergSource

        source = GutenbergSource(
            cache_dir=project_root / "texts" / ".gutenberg_cache"
        )
        output_path = project_root / "texts" / "last_and_first_men_clean.txt"

        path = source.download_and_clean(17662, output_path)
        text = path.read_text(encoding="utf-8")

        print(f"Downloaded: {path}")
        print(f"Size: {len(text):,} characters")
        print(f"Lines: {len(text.splitlines()):,}")
        print(f"First 200 chars: {text[:200]}...")
        print("PASS")
        return True

    except Exception as e:
        print(f"FAIL: {e}")
        return False


def test_parse() -> bool:
    """Test chapter parsing."""
    print("\n" + "=" * 50)
    print("TEST: Chapter Parsing")
    print("=" * 50)

    try:
        from src.sources.text_parser import TextParser

        source_path = project_root / "texts" / "last_and_first_men_clean.txt"
        if not source_path.exists():
            print("Source text not found. Run --download first.")
            return False

        parser = TextParser()
        chapters = parser.parse_file(source_path)

        print(parser.get_chapter_summary(chapters))

        if len(chapters) > 0:
            print(f"\nFirst chapter preview ({chapters[0].title}):")
            print(f"  {chapters[0].text[:300]}...")
            print("\nPASS")
            return True
        else:
            print("FAIL: No chapters parsed")
            return False

    except Exception as e:
        print(f"FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tts() -> bool:
    """Test TTS synthesis on a short sample."""
    print("\n" + "=" * 50)
    print("TEST: TTS Synthesis (short sample)")
    print("=" * 50)

    try:
        from src.audiobook.tts_engine import TTSEngine

        engine = TTSEngine(voice_profile="philosophical_sf")

        test_text = (
            "I am one of the Last Men. I am speaking to you from "
            "the remote future. Two billion years have passed since "
            "your time, and in that vast span humanity has changed "
            "beyond recognition."
        )

        output_path = project_root / "output" / "test" / "tts_test.wav"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"Test text: {test_text[:80]}...")
        print("Loading TTS model (this may take a moment on first run)...")

        start = time.time()
        engine.synthesize_chapter(test_text, output_path)
        elapsed = time.time() - start

        if output_path.exists():
            size_kb = output_path.stat().st_size / 1024
            print(f"Output: {output_path}")
            print(f"Size: {size_kb:.1f} KB")
            print(f"Time: {elapsed:.1f}s")
            print("PASS")
            return True
        else:
            print("FAIL: Output file not created")
            return False

    except ImportError as e:
        print(f"FAIL: Missing dependency - {e}")
        print("  pip install TTS")
        return False
    except Exception as e:
        print(f"FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            engine.unload_model()
        except Exception:
            pass


def test_mastering() -> bool:
    """Test audio mastering."""
    print("\n" + "=" * 50)
    print("TEST: Audio Mastering")
    print("=" * 50)

    test_wav = project_root / "output" / "test" / "tts_test.wav"
    if not test_wav.exists():
        print("Test WAV not found. Run --tts first.")
        return False

    try:
        from src.audiobook.postprocessing import AudioMastering

        mastering = AudioMastering(profile="audiobook_dense")
        output_path = project_root / "output" / "test" / "mastered_test.wav"

        mastering.master_chapter(test_wav, output_path)

        if output_path.exists():
            # Analyze
            stats = mastering.analyze_audio(output_path)
            print(f"Duration: {stats['duration_seconds']:.1f}s")
            print(f"Sample rate: {stats['sample_rate']} Hz")
            print(f"Peak: {stats['peak_ratio']:.3f}")
            print(f"Size: {stats['file_size_mb']:.2f} MB")
            print("PASS")
            return True
        else:
            print("FAIL: Mastered file not created")
            return False

    except ImportError as e:
        print(f"FAIL: Missing dependency - {e}")
        return False
    except Exception as e:
        print(f"FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_packaging() -> bool:
    """Test audiobook packaging."""
    print("\n" + "=" * 50)
    print("TEST: Audiobook Packaging")
    print("=" * 50)

    mastered_dir = project_root / "output" / "test"
    mastered_wav = mastered_dir / "mastered_test.wav"
    if not mastered_wav.exists():
        print("Mastered WAV not found. Run --master first.")
        return False

    try:
        from src.audiobook.packaging import AudiobookPackager, BookMeta

        # Create a fake chapter file with expected naming
        chapter_dir = mastered_dir / "pkg_test_chapters"
        chapter_dir.mkdir(exist_ok=True)

        import shutil
        test_chapter = chapter_dir / "chapter_01.wav"
        shutil.copy2(str(mastered_wav), str(test_chapter))

        packager = AudiobookPackager(
            output_dir=mastered_dir / "pkg_test_output"
        )

        book_meta = BookMeta(
            title="Test Book",
            author="Test Author",
            description="Pipeline test",
        )

        outputs = packager.package_audiobook(
            mastered_dir=chapter_dir,
            book_meta=book_meta,
            chapter_titles=["Test Chapter"],
        )

        print(f"Created {len(outputs)} output files:")
        for name, path in outputs.items():
            print(f"  {name}: {path}")
        print("PASS")
        return True

    except FileNotFoundError as e:
        if "ffmpeg" in str(e):
            print("FAIL: ffmpeg not installed")
            print("  apt install ffmpeg  (Linux)")
            print("  brew install ffmpeg (macOS)")
        else:
            print(f"FAIL: {e}")
        return False
    except Exception as e:
        print(f"FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cover_art() -> bool:
    """Test cover art generation."""
    print("\n" + "=" * 50)
    print("TEST: Cover Art Generation")
    print("=" * 50)

    try:
        from src.audiobook.cover_art import CoverArtGenerator

        generator = CoverArtGenerator()
        output_dir = project_root / "output" / "test" / "covers"

        covers = generator.generate_book_covers(
            book_id="last_and_first_men",
            output_dir=output_dir,
            num_variations=1,  # Just 1 for testing
        )

        if covers and covers[0].exists():
            size_mb = covers[0].stat().st_size / (1024 * 1024)
            print(f"Cover: {covers[0]}")
            print(f"Size: {size_mb:.1f} MB")
            print("PASS")
            return True
        else:
            print("FAIL: Cover not generated")
            return False

    except ImportError as e:
        print(f"FAIL: Missing dependency - {e}")
        return False
    except Exception as e:
        print(f"FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            generator.unload_model()
        except Exception:
            pass


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Test audiobook production pipeline stages",
    )
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--gpu", action="store_true", help="Test GPU")
    parser.add_argument("--download", action="store_true", help="Test download")
    parser.add_argument("--parse", action="store_true", help="Test parsing")
    parser.add_argument("--tts", action="store_true", help="Test TTS")
    parser.add_argument("--master", action="store_true", help="Test mastering")
    parser.add_argument("--package", action="store_true", help="Test packaging")
    parser.add_argument("--cover", action="store_true", help="Test cover art")

    args = parser.parse_args()

    if not any(vars(args).values()):
        parser.print_help()
        print("\nRecommended test order:")
        print("  1. python scripts/test_pipeline.py --gpu")
        print("  2. python scripts/test_pipeline.py --download")
        print("  3. python scripts/test_pipeline.py --parse")
        print("  4. python scripts/test_pipeline.py --tts")
        print("  5. python scripts/test_pipeline.py --master")
        print("  6. python scripts/test_pipeline.py --package")
        print("  7. python scripts/test_pipeline.py --cover")
        return

    results = {}

    tests = [
        ("gpu", args.gpu or args.all, test_gpu),
        ("download", args.download or args.all, test_download),
        ("parse", args.parse or args.all, test_parse),
        ("tts", args.tts or args.all, test_tts),
        ("master", args.master or args.all, test_mastering),
        ("package", args.package or args.all, test_packaging),
        ("cover", args.cover or args.all, test_cover_art),
    ]

    for name, should_run, test_fn in tests:
        if should_run:
            results[name] = test_fn()

    # Summary
    print("\n" + "=" * 50)
    print("PIPELINE TEST RESULTS")
    print("=" * 50)
    for name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {name:12s} {status}")

    all_passed = all(results.values())
    print(f"\nOverall: {'ALL PASSED' if all_passed else 'SOME FAILED'}")

    if not all_passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
