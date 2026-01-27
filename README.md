# Public Domain Monetization System

A complete system for producing AI-generated audiobooks from 1930 works entering US public domain on January 1, 2026.

## Overview

This project leverages local AI (Coqui XTTS-v2) on an RTX 5080 to produce audiobooks at 1/100th the cost of traditional production, targeting distribution through Google Play Books and Findaway Voices.

### Key Advantages
- **100x Cost Reduction**: Local TTS vs cloud ($30-50 vs $3,000-5,000 per title)
- **Hardware Edge**: RTX 5080 produces 2-3 audiobooks per day
- **Multi-Platform**: Findaway (40+ retailers), Google Play, direct sales
- **Analytics Built-In**: Revenue tracking and dashboard system

## Quick Start

```bash
# Clone and setup
git clone git@github.com:dustingregg1/PublicDomainMonetization.git
cd PublicDomainMonetization

# Install dependencies
pip install -r requirements.txt

# Install TTS (GPU)
pip install TTS torch --index-url https://download.pytorch.org/whl/cu121

# Produce an audiobook
python -m src.audiobook.pipeline \
  --input texts/maltese_falcon_clean.txt \
  --output output/maltese_falcon \
  --voice-profile hardboiled_detective \
  --book-id maltese_falcon_2026 \
  --title "The Maltese Falcon"
```

## Launch Titles

| Title | Author | Status | Est. Hours | PD Status |
|-------|--------|--------|------------|-----------|
| The Maltese Falcon | Dashiell Hammett | Production Kit Ready | 15-18 | US: Jan 2026, EU: 2032 |
| Strong Poison | Dorothy L. Sayers | Production Kit Ready | 16-19 | US: Jan 2026, EU: 2028 |
| Last and First Men | Olaf Stapledon | Production Kit Ready | 21-23 | **GLOBAL PD** (died 1950) |

See `kits/<title>/PRODUCTION_KIT.md` for complete production guides.

## System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     AUDIOBOOK PIPELINE                        │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐        │
│   │    TEXT     │   │     TTS     │   │   AUDIO     │        │
│   │ PROCESSING  │──▶│  SYNTHESIS  │──▶│  MASTERING  │        │
│   └─────────────┘   └─────────────┘   └─────────────┘        │
│         │                 │                  │                │
│         ▼                 ▼                  ▼                │
│   - OCR cleanup     - Coqui XTTS-v2   - ACX compliance       │
│   - Chapter split   - ElevenLabs      - Noise reduction      │
│   - Dialogue detect - Voice profiles  - M4B export           │
│                                                               │
├──────────────────────────────────────────────────────────────┤
│                    DISTRIBUTION SYSTEM                        │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐        │
│   │  FINDAWAY   │   │ GOOGLE PLAY │   │   DIRECT    │        │
│   │   VOICES    │   │   BOOKS     │   │   SALES     │        │
│   └─────────────┘   └─────────────┘   └─────────────┘        │
│       70% royalty       70% royalty       95% margin         │
│       40+ platforms     Global reach      Gumroad/Payhip     │
│                                                               │
├──────────────────────────────────────────────────────────────┤
│                    ANALYTICS DASHBOARD                        │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│   Revenue Tracking | Goal Progress | Projections | Reports   │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

## Project Structure

```
PublicDomainMonetization/
├── src/
│   ├── audiobook/
│   │   ├── pipeline.py              # Main orchestrator
│   │   ├── preprocessing/           # Text processing
│   │   ├── tts/                     # TTS engines & voice profiles
│   │   ├── postprocessing/          # Audio mastering
│   │   ├── distribution/            # Platform uploaders
│   │   └── config/                  # YAML configurations
│   ├── analytics/
│   │   ├── revenue_tracker.py       # Sales tracking
│   │   └── analytics_dashboard.py   # Reports & visualization
│   └── agents/                      # Specialized AI agents
├── kits/
│   ├── maltese_falcon/              # Maltese Falcon production kit
│   ├── strong_poison/               # Strong Poison production kit
│   ├── last_and_first_men/          # Last and First Men production kit
│   └── COMPLETE_PRODUCTION_KIT.md   # General production guide
├── docs/
│   ├── WORKFLOW_GUIDE.md            # Step-by-step workflow
│   ├── AGENT_SWARM_ARCHITECTURE.md  # Agent system design
│   └── research/                    # Market research
├── scripts/
│   └── cleanup_text.py              # Text preprocessing
└── tests/
```

## Revenue Projections

### Conservative (Year 1)

| Month | Titles Live | Monthly Revenue |
|-------|-------------|-----------------|
| 1-2 | 1 | $250-300 |
| 3-4 | 2 | $500-600 |
| 5-6 | 3 | $750-900 |
| 7-12 | 3+ | $1,000-1,500 |

**Conservative Year 1 Total: $6,000-10,000**

### Realistic (Validated by 6-AI Review)

| Outcome | Probability |
|---------|------------|
| Total failure | 30% |
| Modest success ($500-1,500/mo) | 40% |
| Good success ($2,000-4,000/mo) | 20% |
| Great success ($5,000+/mo) | 10% |

## Requirements

### Hardware
- NVIDIA GPU with 16GB+ VRAM (RTX 5080 recommended)
- 32GB+ RAM
- Fast SSD storage

### Software
- Python 3.11+
- CUDA toolkit
- FFmpeg

### Accounts (Free to Create)
- Findaway Voices Publisher Account
- Google Play Books Partner Account
- Gumroad/Payhip (optional, for direct sales)

## Key Documentation

| Document | Purpose |
|----------|---------|
| [WORKFLOW_GUIDE.md](docs/WORKFLOW_GUIDE.md) | Complete step-by-step workflow |
| [MASTERPLAN_V2.md](MASTERPLAN_V2.md) | Full strategy document |
| [MARKET_REALITY_CHECK.md](MARKET_REALITY_CHECK.md) | 6-AI contrarian analysis |
| [FINAL_PLAN_FOR_WIFE.md](FINAL_PLAN_FOR_WIFE.md) | Wife-explainable summary |

## Analytics Dashboard

```python
from src.analytics.revenue_tracker import RevenueTracker
from src.analytics.analytics_dashboard import AnalyticsDashboard

tracker = RevenueTracker()
dashboard = AnalyticsDashboard(tracker)

# CLI summary
dashboard.print_summary()

# Generate HTML dashboard
dashboard.generate_html_dashboard()
```

## Legal Notes

- All works must be verified as US public domain before production
- EU distribution may be restricted (life+70 years rule)
- Trademark considerations documented in production kits
- NOT legal advice - consult attorney for specific situations

## Contributing

This is a personal monetization project. Issues and suggestions welcome via GitHub.

## License

MIT License - See LICENSE file for details.

---

*Built with Claude Code, leveraging local AI for 100x cost reduction in audiobook production.*
