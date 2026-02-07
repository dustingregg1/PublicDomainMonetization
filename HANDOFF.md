# Session Handoff - Public Domain Monetization Project

**Date:** February 7, 2026
**Hardware:** Moving to ROG Strix G18 with RTX 5080 (16GB VRAM)
**Status:** Ready for first audiobook production

---

## IMMEDIATE NEXT STEP

On the new laptop with RTX 5080:

```bash
# 1. Clone the repo (or OneDrive will have synced it)
cd ~/Desktop/PublicDomainMonetization

# 2. Install dependencies
pip install TTS pydub librosa soundfile

# 3. Install Ollama for local LLM
# Download from https://ollama.ai

# 4. Download source text
# Last and First Men from Project Gutenberg: https://www.gutenberg.org/ebooks/17662

# 5. Test GPU access
python -c "import torch; print(torch.cuda.is_available())"

# 6. Run first production
python scripts/run_overnight.py --book last_and_first_men
python scripts/run_overnight.py --run
```

---

## What Was Built This Session (Feb 7, 2026)

### 1. Critical Review & Legal Hardening
- `CRITICAL_REVIEW.md` - Gap analysis vs Gemini research
- All 3 production kits updated with:
  - Mandatory disclaimer templates
  - Trade dress avoidance checklists
  - EU territory blocking instructions
  - Character descriptions FROM NOVELS (not movies)
  - Negative prompts for AI cover art

### 2. RTX 5080 Automation Infrastructure
```
src/automation/
├── __init__.py
├── gpu_orchestrator.py   # GPU task queue, VRAM management
└── batch_processor.py    # Full audiobook batch production

scripts/
└── run_overnight.py      # CLI for overnight batch processing
```

**Usage:**
```bash
python scripts/run_overnight.py --book all    # Queue all books
python scripts/run_overnight.py --run         # Start overnight production
python scripts/run_overnight.py --status      # Check GPU/queue status
python scripts/run_overnight.py --resume      # Resume interrupted jobs
```

### 3. Revised Launch Order
| Priority | Title | Author | Risk | Notes |
|----------|-------|--------|------|-------|
| **1st** | Last and First Men | Stapledon | LOWEST | Global PD, validates pipeline |
| **2nd** | The Maltese Falcon | Hammett | LOW | High demand, EU block 2032 |
| **3rd** | Strong Poison | Sayers | LOW | British voice, EU block 2028 |

**Rationale:** Start with zero-risk title to validate pipeline before higher-profile works.

### 4. Character Chatbot MVP Architecture
- `docs/CHATBOT_MVP.md` - Complete technical spec
- "Hire Sam Spade" detective roleplay concept
- Runs on RTX 5080 with Ollama + Llama 3 8B
- Revenue potential: $1,000-5,000/month

---

## Key Insights from Critical Review

1. **Audiobook-only is too narrow** - Need diversification (chatbots, Kickstarter)
2. **Sam Spade is BLOND** in the book (not dark-haired like Bogart)
3. **Christie is risky** - EU block until 2047, active estate
4. **Marketing budget needed** - Plan for $500 initial allocation
5. **EU blocking is required** - Must operationalize for Hammett/Sayers

---

## Files Structure

```
PublicDomainMonetization/
├── HANDOFF.md              # THIS FILE - read first on new machine
├── CRITICAL_REVIEW.md      # Gap analysis and recommendations
├── kits/
│   ├── maltese_falcon/PRODUCTION_KIT.md   # +Legal hardening
│   ├── strong_poison/PRODUCTION_KIT.md    # +Legal hardening
│   └── last_and_first_men/PRODUCTION_KIT.md  # +Legal hardening
├── docs/
│   ├── TITLE_QUEUE.md      # Revised launch order
│   ├── CHATBOT_MVP.md      # Chatbot architecture
│   └── WORKFLOW_GUIDE.md   # Production workflow
├── src/
│   ├── automation/         # GPU orchestration (NEW)
│   ├── analytics/          # Revenue tracking
│   └── audiobook/          # TTS pipeline (scaffolding)
└── scripts/
    └── run_overnight.py    # Overnight batch CLI (NEW)
```

---

## Accounts Ready

| Platform | Status | Purpose |
|----------|--------|---------|
| Findaway Voices | Created | 70% royalty distribution |
| Google Play Books | Created | Direct publishing |
| Gumroad | Created | 95% margin direct sales |
| Kit (ConvertKit) | Created | Email list building |

---

## What Still Needs Doing

### Before First Production
- [ ] Install TTS dependencies (Coqui XTTS-v2)
- [ ] Install Ollama + Llama 3 8B
- [ ] Download "Last and First Men" source text
- [ ] Test full pipeline with one chapter
- [ ] Generate cover art

### Production Phase
- [ ] Produce Last and First Men (February)
- [ ] Produce The Maltese Falcon (March)
- [ ] Produce Strong Poison (April)

### Parallel Track
- [ ] Begin chatbot MVP development (February)
- [ ] Sam Spade beta launch (June)

---

## Quick Context for Claude on New Machine

Tell Claude:
```
I'm continuing the Public Domain Monetization project. Read HANDOFF.md and
CRITICAL_REVIEW.md for full context. I have an RTX 5080 laptop now.

Next step: Install dependencies and produce "Last and First Men" audiobook.
```

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

*Handoff created: February 7, 2026*
*Ready for production on RTX 5080 laptop*
