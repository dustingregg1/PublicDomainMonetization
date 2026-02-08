# Session Handoff - Public Domain Monetization Project

**Date:** February 7, 2026
**Hardware:** ROG Strix G18 with RTX 5080 (16GB VRAM)
**Status:** Full pipeline built - ready for first audiobook production

---

## IMMEDIATE NEXT STEP

Source text downloaded, chapters parsed, all deps installed. On RTX 5080:

```bash
# One-shot setup (installs deps, downloads model, runs smoke test)
python scripts/setup_first_run.py

# Or step by step:
python scripts/test_pipeline.py --gpu       # Verify CUDA
python scripts/test_pipeline.py --parse     # Verify chapters (should say 16)
python scripts/test_pipeline.py --tts       # Test TTS on short sample
python scripts/test_pipeline.py --master    # Test audio mastering
python scripts/test_pipeline.py --package   # Test MP3/M4B output

# Full production run
python scripts/run_overnight.py --book last_and_first_men
python scripts/run_overnight.py --run
```

---

## What Was Built

### Session 1: Planning & Legal Framework
- Production kits for 3 titles with legal hardening
- Critical review and gap analysis
- Account setup (Findaway, Google Play, Gumroad, Kit)

### Session 3: Dependencies, Source Text, Unicode Fix (Current)
- All pip deps installed (PyTorch 2.10+cu128, TTS 0.22.0, diffusers 0.36.0)
- Downloaded Last and First Men from GitHub EPUB repo (Gutenberg proxy-blocked)
- Fixed chapter parser for Unicode Roman numerals (Ⅰ→I, Ⅱ→II, etc.)
- 35 unit tests passing (including 2 new Unicode tests)
- pandas pinned to <2.0 (TTS 0.22.0 requirement)
- numpy pinned to 1.26.x (pandas 1.5.x binary compat)
- Added setup_first_run.py for one-shot model download + smoke test

### Session 2: Full Production Pipeline

**New modules created:**
```
src/sources/
├── __init__.py
├── gutenberg.py           # Download from Project Gutenberg, strip headers
└── text_parser.py         # Parse chapters from raw text

src/audiobook/
├── __init__.py
├── tts_engine.py          # Coqui XTTS-v2 TTS synthesis
├── postprocessing.py      # Audio normalization, mastering
├── packaging.py           # MP3/M4B creation with chapter markers
└── cover_art.py           # Stable Diffusion XL cover generation

src/automation/
├── gpu_orchestrator.py    # GPU task queue (NOW WIRED TO REAL CODE)
└── batch_processor.py     # Batch production (NOW WIRED TO REAL CODE)

scripts/
├── run_overnight.py       # Overnight production CLI (REAL PARSING)
└── test_pipeline.py       # Stage-by-stage pipeline validation

texts/
└── last_and_first_men_clean.txt  # 115K words, 16 chapters parsed

tests/
├── test_sources/          # Gutenberg + parser tests (28 passing)
└── test_audiobook/        # TTS engine unit tests (7 passing)
```

**Key changes from scaffolding to real code:**
- `gpu_orchestrator.py` now calls real TTS, SDXL, and mastering code
- `batch_processor.py` now parses real chapters and calls real synthesis
- `run_overnight.py` downloads from Gutenberg and parses chapter structure
- Voice profiles configured per book genre (philosophical, hardboiled, British)
- Trade dress avoidance baked into cover art negative prompts

---

## Pipeline Flow

```
Gutenberg Download → Chapter Parsing → TTS Synthesis → Audio Mastering → Packaging
                                            ↓                               ↓
                                      Cover Art Gen              MP3 + M4B + Metadata
```

### Voice Profiles
| Book | Profile | Speed | Style |
|------|---------|-------|-------|
| Last and First Men | `philosophical_sf` | 0.92x | Contemplative, measured |
| Maltese Falcon | `hardboiled_detective` | 1.0x | Direct, noir tone |
| Strong Poison | `golden_age_british` | 0.95x | Refined, period British |

### Mastering Profiles
| Book | Profile | Target LUFS | Silence |
|------|---------|-------------|---------|
| Last and First Men | `audiobook_dense` | -15 dB | 400-1000ms |
| Maltese Falcon | `audiobook_dramatic` | -16 dB | 250-600ms |
| Strong Poison | `audiobook_standard` | -16 dB | 300-800ms |

---

## Launch Order
| Priority | Title | Author | Risk | Notes |
|----------|-------|--------|------|-------|
| **1st** | Last and First Men | Stapledon | LOWEST | Global PD, validates pipeline |
| **2nd** | The Maltese Falcon | Hammett | LOW | High demand, EU block 2032 |
| **3rd** | Strong Poison | Sayers | LOW | British voice, EU block 2028 |

---

## What Still Needs Doing

### Before First Production (On RTX 5080 Laptop)
- [x] Install all dependencies (`pip install -r requirements.txt`)
- [x] Install CUDA PyTorch (2.10+cu128)
- [x] Install ffmpeg
- [x] Download source text (Last and First Men - 115K words, 16 chapters)
- [x] Fix Unicode chapter parsing
- [x] 35/35 unit tests passing
- [ ] Run `python scripts/setup_first_run.py` (downloads XTTS-v2 model)
- [ ] Run `test_pipeline.py --tts` (GPU smoke test)
- [ ] First full production of Last and First Men

### Production Phase
- [ ] Produce Last and First Men (February)
- [ ] QA pass - listen to philosophical passages
- [ ] Upload to Findaway, Google Play, Gumroad
- [ ] Produce The Maltese Falcon (March) - need source text manually
- [ ] Produce Strong Poison (April) - need source text manually

### Parallel Track
- [ ] Character chatbot MVP (docs/CHATBOT_MVP.md)
- [ ] Marketing - $500 initial budget, target SF communities

---

## Technical Notes

### RTX 5080 VRAM Allocation
| Task | VRAM Needed |
|------|-------------|
| Coqui XTTS-v2 TTS | 6 GB |
| Llama 3 8B (Ollama) | 8 GB |
| Stable Diffusion XL | 10 GB |
| Audio mastering | 2 GB |

16GB total = Can run TTS + LLM simultaneously, or image gen alone

### Key Legal Points
- Sam Spade not copyrightable (Warner Bros. v. CBS, 1954)
- Use BOOK descriptions, not movie imagery
- Block EU for Hammett (until 2032) and Sayers (until 2028)
- Stapledon is GLOBAL PD - no restrictions

---

*Handoff updated: February 8, 2026*
*Full pipeline built + deps installed + source text downloaded - 35 unit tests passing*
