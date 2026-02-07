# Session Handoff - Public Domain Monetization Project

**Date:** February 7, 2026
**Hardware:** ROG Strix G18 with RTX 5080 (16GB VRAM)
**Status:** Full pipeline built - ready for first audiobook production

---

## IMMEDIATE NEXT STEP

Install dependencies and run the production pipeline:

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# For CUDA GPU support (recommended):
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 2. Install ffmpeg (required for audio packaging)
apt install ffmpeg  # Linux
# brew install ffmpeg  # macOS

# 3. Verify GPU
python -c "import torch; print(torch.cuda.is_available())"

# 4. Test pipeline stages
python scripts/test_pipeline.py --gpu
python scripts/test_pipeline.py --download
python scripts/test_pipeline.py --parse
python scripts/test_pipeline.py --tts        # Requires TTS installed
python scripts/test_pipeline.py --master     # Requires pydub + ffmpeg
python scripts/test_pipeline.py --package    # Requires ffmpeg

# 5. Full production run
python scripts/run_overnight.py --download last_and_first_men
python scripts/run_overnight.py --book last_and_first_men
python scripts/run_overnight.py --run
```

---

## What Was Built

### Session 1: Planning & Legal Framework
- Production kits for 3 titles with legal hardening
- Critical review and gap analysis
- Account setup (Findaway, Google Play, Gumroad, Kit)

### Session 2: Full Production Pipeline (Current)

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

tests/
├── test_sources/          # Gutenberg + parser tests (33 passing)
└── test_audiobook/        # TTS engine unit tests
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
- [ ] Install all dependencies (`pip install -r requirements.txt`)
- [ ] Install CUDA PyTorch
- [ ] Install ffmpeg
- [ ] Run `test_pipeline.py --all` to verify
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

*Handoff updated: February 7, 2026*
*Full pipeline built - 33 unit tests passing*
