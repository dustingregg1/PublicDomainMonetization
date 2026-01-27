# Public Domain Audiobook Production - Complete Workflow Guide

## Overview

This guide walks you through the complete process of producing and distributing AI-generated audiobooks from public domain content.

---

## Quick Start (For Launch Titles)

### Prerequisites

1. **Hardware**: NVIDIA GPU with 16GB+ VRAM (RTX 5080 recommended)
2. **Software**:
   - Python 3.11+
   - CUDA toolkit
   - FFmpeg
3. **Accounts**:
   - Findaway Voices Publisher Account
   - Google Play Books Partner Account
   - Gumroad/Payhip for direct sales (optional)

### Installation

```bash
# Clone repository
git clone git@github.com:dustingregg1/PublicDomainMonetization.git
cd PublicDomainMonetization

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install TTS dependencies (GPU)
pip install TTS torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

---

## Complete Production Pipeline

### Phase 1: Text Acquisition & Preparation

#### Step 1.1: Download Source Text
```bash
# Example for Maltese Falcon
# Visit: https://archive.org/details/maltesefalcon0000hamm
# Download OCR text version

# Or use Project Gutenberg for older works
# Example: https://www.gutenberg.org/ebooks/17662 (Last and First Men)
```

#### Step 1.2: Clean the Text
```bash
python scripts/cleanup_text.py \
  --input texts/raw/maltese_falcon_raw.txt \
  --output texts/clean/maltese_falcon_clean.txt \
  --fix-ocr \
  --preserve-british  # If applicable
```

The cleanup script handles:
- OCR error correction (rn→m, 1→l, etc.)
- Quotation mark normalization
- Chapter detection and marking
- Paragraph restoration
- Dialogue tag cleanup

#### Step 1.3: Verify Text Quality
```bash
python -m src.audiobook.pipeline \
  --input texts/clean/maltese_falcon_clean.txt \
  --preview-only

# Output shows:
# - Detected chapters
# - Word count per chapter
# - Estimated audio duration
# - Potential issues
```

---

### Phase 2: Voice Profile Configuration

#### Step 2.1: Choose Voice Profile

Available presets in `src/audiobook/tts/voice_profiles.py`:

| Profile | Best For | Accent |
|---------|----------|--------|
| `hardboiled_detective` | Noir, mystery | American |
| `golden_age_british` | Sayers, Christie | British RP |
| `philosophical_sf` | Stapledon, Wells | Neutral/British |
| `classic_narrator` | General classics | Neutral |
| `southern_gothic` | Faulkner, etc. | American South |

#### Step 2.2: Test Voice Profile
```bash
python -m src.audiobook.tts.tts_engine \
  --test "Sam Spade's jaw was long and bony, his chin a jutting v." \
  --voice hardboiled_detective \
  --output test_output.wav
```

Listen to test_output.wav and adjust settings if needed.

#### Step 2.3: Custom Voice (Optional)

For voice cloning:
```python
from src.audiobook.tts.voice_profiles import VoiceProfileManager

manager = VoiceProfileManager()
manager.create_profile(
    profile_id="custom_narrator",
    name="My Custom Voice",
    sample_paths=["samples/my_voice_sample.wav"],  # 10-30 sec clean audio
    genres=["mystery", "thriller"],
)
```

---

### Phase 3: Audio Production

#### Step 3.1: Run Full Pipeline
```bash
python -m src.audiobook.pipeline \
  --input texts/clean/maltese_falcon_clean.txt \
  --output output/maltese_falcon \
  --voice-profile hardboiled_detective \
  --book-id maltese_falcon_2026 \
  --title "The Maltese Falcon"
```

Pipeline stages:
1. **Text Processing** - Chapter splitting, normalization
2. **TTS Synthesis** - Chapter-by-chapter generation
3. **Audio Mastering** - ACX compliance, noise reduction
4. **Export** - MP3 chapters + M4B audiobook

#### Step 3.2: Monitor Progress

The pipeline provides callbacks:
```
Processing text: 100%
Selecting voice: 100%
Synthesizing audio: 45% (Chapter 9/20)
```

Estimated time on RTX 5080:
- ~15 minutes per hour of final audio
- 8-hour audiobook = ~2 hours synthesis time

#### Step 3.3: GPU Optimization

For maximum throughput:
```python
from src.audiobook.pipeline import AudiobookPipeline, PipelineConfig

config = PipelineConfig(
    use_gpu=True,
    gpu_device=0,  # First GPU
    # Enable batch processing
)

pipeline = AudiobookPipeline(config)
```

---

### Phase 4: Quality Assurance

#### Step 4.1: Automated Checks
```bash
python scripts/qa_check.py output/maltese_falcon/final/maltese_falcon_2026.m4b
```

Checks for:
- Audio levels (ACX compliance: -23dB to -18dB RMS)
- Noise floor (-60dB or lower)
- Chapter markers present
- No clipping or distortion

#### Step 4.2: Manual Review Checklist

- [ ] Listen to first chapter completely
- [ ] Spot-check 3-4 random chapters
- [ ] Verify difficult pronunciations:
  - Character names
  - Place names
  - Foreign phrases
- [ ] Check pacing for dialogue sections
- [ ] Verify chapter transitions are smooth
- [ ] Confirm no TTS artifacts (robotic sounds, mispronunciations)

#### Step 4.3: Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| Robotic sound | Adjust emotion settings, try different voice |
| Wrong pronunciation | Add to pronunciation dictionary |
| Pacing too fast/slow | Adjust speed parameter |
| Chapter break issues | Check text preprocessing markers |
| Noise/artifacts | Re-run mastering with different settings |

---

### Phase 5: Cover Art Generation

#### Step 5.1: Generate Cover Art
```bash
# Using Stable Diffusion locally
python scripts/generate_cover.py \
  --title "The Maltese Falcon" \
  --author "Dashiell Hammett" \
  --style "art_deco_noir" \
  --output output/maltese_falcon/assets/cover.png
```

#### Step 5.2: Verify Dimensions
- Findaway: 2400x2400 minimum
- Google Play: 1600x2400 minimum
- Generate at 3000x3000 for flexibility

#### Step 5.3: Add Text Overlays
```bash
python scripts/add_cover_text.py \
  --image output/maltese_falcon/assets/cover_base.png \
  --title "THE MALTESE FALCON" \
  --author "DASHIELL HAMMETT" \
  --output output/maltese_falcon/assets/cover_final.png
```

---

### Phase 6: Distribution

#### Step 6.1: Prepare Metadata

See production kit for your title. Key fields:
- Title with subtitle
- Description (short + long)
- Categories (BISAC codes)
- Keywords
- Price points by platform

#### Step 6.2: Upload to Platforms

**Findaway Voices:**
```bash
python -m src.audiobook.distribution.findaway_uploader \
  --config src/audiobook/distribution/platforms.yaml \
  --audio output/maltese_falcon/final/ \
  --cover output/maltese_falcon/assets/cover_2400x2400.jpg \
  --metadata output/maltese_falcon/metadata/findaway_metadata.json
```

**Google Play:**
```bash
python -m src.audiobook.distribution.google_play_publisher \
  --config src/audiobook/distribution/platforms.yaml \
  --audio output/maltese_falcon/final/ \
  --cover output/maltese_falcon/assets/cover_1600x2400.jpg \
  --metadata output/maltese_falcon/metadata/google_play_metadata.json
```

#### Step 6.3: Verify Uploads
- Check platform dashboards
- Verify all chapters uploaded
- Confirm metadata displays correctly
- Test audio sample playback

---

### Phase 7: Revenue Tracking

#### Step 7.1: Register Book
```python
from src.analytics.revenue_tracker import RevenueTracker, Platform
from decimal import Decimal
from datetime import date

tracker = RevenueTracker()

tracker.register_book(
    book_id="maltese_falcon_2026",
    title="The Maltese Falcon",
    author="Dashiell Hammett",
    production_cost=Decimal("50"),
    publish_date=date(2026, 1, 15),
    platforms=["findaway_voices", "google_play", "direct_gumroad"],
)
```

#### Step 7.2: Import Sales Data

Monthly, download CSV reports from each platform and import:
```python
# Findaway
tracker.import_findaway_csv("reports/findaway_jan_2026.csv")

# Google Play
tracker.import_google_play_csv("reports/google_play_jan_2026.csv")

# Gumroad
tracker.import_gumroad_csv("reports/gumroad_jan_2026.csv")
```

#### Step 7.3: Generate Reports
```python
from src.analytics.analytics_dashboard import AnalyticsDashboard

dashboard = AnalyticsDashboard(tracker)

# CLI summary
dashboard.print_summary()

# Monthly report
dashboard.print_monthly_report(2026, 1)

# Export dashboard
outputs = dashboard.export_all()
print(f"Dashboard: {outputs['html']}")
```

---

## Production Schedule (Launch Titles)

### Week 1: The Maltese Falcon
| Day | Task | Hours |
|-----|------|-------|
| Mon | Download source, cleanup | 2 |
| Tue | Voice setup, test | 2 |
| Wed | TTS synthesis (GPU) | 4 |
| Thu | QA, mastering | 3 |
| Fri | Cover art | 1 |
| Sat | Upload, verify | 2 |
| **Total** | | **14** |

### Week 2: Strong Poison
| Day | Task | Hours |
|-----|------|-------|
| Mon | Source, cleanup | 2 |
| Tue | British voice testing | 2 |
| Wed-Thu | TTS synthesis | 5 |
| Fri | QA (focus accents) | 3 |
| Sat | Cover, upload | 2 |
| **Total** | | **14** |

### Week 3: Last and First Men
| Day | Task | Hours |
|-----|------|-------|
| Mon | Source (Gutenberg - clean) | 1 |
| Tue | Contemplative voice setup | 2 |
| Wed-Fri | TTS synthesis (longer book) | 7 |
| Sat | QA, species guide PDF | 3 |
| Sun | Cover, upload | 2 |
| **Total** | | **15** |

---

## Automation Tips

### Batch Processing
```bash
# Process multiple books overnight
python scripts/batch_produce.py \
  --config batch_config.yaml \
  --parallel 2  # Process 2 books at once
```

### Scheduled Tasks
```bash
# Example cron job for daily revenue import
0 8 * * * cd /path/to/project && python scripts/import_daily_sales.py
```

### Monitoring
```bash
# Check GPU utilization
nvidia-smi -l 5  # Every 5 seconds

# Monitor audio output directory
watch -n 30 'ls -la output/*/final/'
```

---

## Troubleshooting

### TTS Issues

**Problem:** CUDA out of memory
```bash
# Reduce batch size in config
# Or process fewer chapters at once
python -m src.audiobook.pipeline --max-batch-size 2
```

**Problem:** Voice sounds robotic
- Try different voice profile
- Adjust emotion/speed settings
- Ensure clean source audio for cloning

### Upload Issues

**Problem:** Findaway rejects files
- Check audio specs match requirements
- Verify cover dimensions
- Ensure metadata is complete

**Problem:** Google Play processing fails
- Re-encode audio with exact spec
- Check for special characters in metadata

### Legal Issues

**Problem:** Copyright claim received
1. Don't panic
2. Gather documentation:
   - Publication date evidence
   - PD status verification
   - Your original content additions
3. Submit counter-claim with evidence
4. Wait for review (usually 3-5 business days)

---

## Next Steps After Launch

1. **Monitor first week sales** - Adjust pricing if needed
2. **Gather reviews** - Reach out to book bloggers
3. **Track analytics** - Weekly dashboard review
4. **Plan next titles** - Research upcoming PD works
5. **Build email list** - Announce new releases

---

## Support

- Production Kits: `kits/<title>/PRODUCTION_KIT.md`
- Technical Docs: `docs/`
- Revenue Tracking: `src/analytics/`
- GitHub Issues: https://github.com/dustingregg1/PublicDomainMonetization/issues
