# The Maltese Falcon - Production Kit

## Quick Reference

| Field | Value |
|-------|-------|
| **Title** | The Maltese Falcon |
| **Author** | Dashiell Hammett |
| **Original Publication** | 1930 (Knopf) |
| **PD Status** | US Public Domain as of January 1, 2026 |
| **Genre** | Hardboiled Detective/Mystery/Noir |
| **Target Duration** | 7-8 hours (audiobook) |
| **Word Count** | ~64,000 words |
| **Priority** | Tier 1 - Launch Title |

---

## Legal Clearance Summary

### Public Domain Status
- **Publication Date**: 1930 (Alfred A. Knopf)
- **Copyright Registration**: Yes, but expired after 95 years
- **US PD Date**: January 1, 2026
- **EU PD Date**: January 1, 2032 (Hammett died 1961 + 70 years)

### Character Trademark Analysis
- **Sam Spade**: NOT copyrightable per Warner Bros. v. CBS (1954)
- **The Maltese Falcon** (the object): Generic term, no trademark issues
- **Film Imagery**: AVOID - Bogart likeness is protected

### Safe to Use
- All original 1930 text
- Character names (Sam Spade, Brigid O'Shaughnessy, Casper Gutman, Joel Cairo)
- Plot elements, dialogue, setting descriptions
- Period-accurate imagery (1930s San Francisco)

### AVOID
- Any film-related imagery (1941 movie)
- Humphrey Bogart likeness
- Movie poster recreations
- Warner Bros. film stills

---

## Source Text Information

### Recommended Source
- **Source**: Internet Archive
- **URL**: https://archive.org/details/maltesefalcon0000hamm
- **Edition**: 1930 First Edition (Knopf)
- **Format**: OCR text available, requires cleanup

### Text Processing Notes
- OCR quality: Good but needs cleanup
- Common OCR errors: "rn" → "m", "l" → "1", quotation marks inconsistent
- Dialogue-heavy: ~60% dialogue
- Chapter structure: 20 chapters, clear breaks

---

## Voice Profile Recommendation

### Primary Voice: Hardboiled Male Narrator
```yaml
voice_profile:
  name: "Sam Noir"
  genre: hardboiled_detective
  settings:
    pitch: -2  # Slightly lower
    speed: 0.95  # Slightly slower for gravitas
    emotion: cynical_detached
  characteristics:
    - Gravelly undertone
    - Clipped delivery for dialogue
    - World-weary affect
    - Period-appropriate cadence
```

### Alternative: Neutral Professional
- Use if hardboiled voice testing reveals quality issues
- Coqui XTTS-v2 default with minor speed adjustment

---

## Chapter Breakdown

| Chapter | Title/Opening | Word Count | Key Scenes |
|---------|---------------|------------|------------|
| 1 | "Samuel Spade's jaw was long..." | ~3,200 | Miss Wonderly arrives |
| 2 | "A telephone bell rang in..." | ~3,100 | Miles Archer killed |
| 3 | "In his bedroom that was..." | ~3,000 | Police interrogation |
| 4 | "When Spade returned to his..." | ~3,400 | Office scene, lying begins |
| 5 | "In his room at the Coronet..." | ~3,200 | Cairo's first appearance |
| 6 | "Spade said, 'Well, I'll be...'" | ~3,100 | Brigid reveals more |
| 7 | "Next morning, when Spade..." | ~3,500 | Investigating |
| 8 | "Spade pulled the victrola..." | ~3,000 | Cairo at apartment |
| 9 | "Spade left the courthouse..." | ~3,200 | Iva Archer |
| 10 | "Spade went through Brigid's..." | ~3,100 | La Paloma mentioned |
| 11 | "Brigid O'Shaughnessy was..." | ~3,400 | Suspicion builds |
| 12 | "Spade, sitting alone with..." | ~3,000 | Thinking scene |
| 13 | "When Spade reached his office..." | ~3,200 | Cairo returns |
| 14 | "It was twelve-thirty when..." | ~3,100 | Dinner scene |
| 15 | "Gutman shook his head..." | ~3,500 | First Gutman meeting |
| 16 | "At twenty minutes to one..." | ~3,300 | The drugging |
| 17 | "When Spade awoke the..." | ~3,100 | After drugging |
| 18 | "A telephone bell wakened..." | ~3,400 | La Paloma arrives |
| 19 | "Spade was eating a sandwich..." | ~3,200 | Wilmer scenes |
| 20 | "They had settled nothing..." | ~4,500 | Final confrontation |

**Total Estimated Word Count**: ~64,000

---

## Audiobook Production Checklist

### Pre-Production
- [ ] Download source text from Internet Archive
- [ ] Run text cleanup script: `python scripts/cleanup_text.py maltese_falcon_raw.txt maltese_falcon_clean.txt`
- [ ] Verify chapter breaks detected correctly
- [ ] Review any flagged OCR issues
- [ ] Select/confirm voice profile

### Production
- [ ] Run pipeline with production config:
```bash
python -m src.audiobook.pipeline \
  --input texts/maltese_falcon_clean.txt \
  --output output/maltese_falcon \
  --voice-profile hardboiled_detective \
  --book-id maltese_falcon_2026 \
  --title "The Maltese Falcon"
```

### Quality Assurance
- [ ] Listen to first chapter completely
- [ ] Spot-check chapters 5, 10, 15, 20
- [ ] Verify dialogue pacing
- [ ] Check for pronunciation issues:
  - "O'Shaughnessy" (oh-SHAW-ness-ee)
  - "Gutman" (GUT-man, not GOOT-man)
  - "Cairo" (KAY-roh, like the city)
  - "La Paloma" (lah pah-LOH-mah)
- [ ] Verify ACX compliance (if repurposing later)
- [ ] Test M4B chapter markers

### Post-Production
- [ ] Export MP3 chapters (individual files)
- [ ] Export M4B audiobook (single file with chapters)
- [ ] Generate cover art
- [ ] Prepare metadata files

---

## Distribution Metadata

### Title & Description

**Full Title**: The Maltese Falcon (Unabridged)

**Subtitle**: A Sam Spade Mystery - Digitally Narrated Edition

**Description** (500 chars max for some platforms):
```
When a beautiful woman walks into Sam Spade's office asking for help,
the hard-boiled San Francisco detective finds himself caught in a web
of lies, murder, and obsession surrounding a legendary black statuette.
This 1930 masterpiece from Dashiell Hammett defined the detective genre
and introduced one of fiction's most iconic private eyes.
```

**Long Description** (2000 chars):
```
Sam Spade had no idea that the elegant woman who called herself
Miss Wonderly would change his life forever. When his partner Miles
Archer is murdered on a case she brought them, Spade finds himself
drawn into a deadly quest for a fabulous prize—a jewel-encrusted
falcon dating back to the Knights of Malta.

First published in 1930, Dashiell Hammett's The Maltese Falcon is the
detective novel that launched a thousand imitations and none have ever
come close. Sam Spade—tough, cynical, but with his own code of honor—
became the template for every hardboiled detective who followed.

This digitally narrated edition brings Hammett's crackling dialogue and
atmospheric San Francisco setting to vivid life. Experience the original
text that inspired the legendary 1941 film, now available as an audiobook
for the first time since entering the public domain.

Perfect for fans of:
• Classic detective fiction
• Film noir enthusiasts
• Raymond Chandler readers
• Golden Age mystery lovers
• American literature students
```

### Categories & Keywords

**Primary Category**: Fiction > Mystery & Detective > Traditional
**Secondary Categories**:
- Fiction > Classics
- Fiction > Noir
- Fiction > Crime

**Keywords** (7):
1. hardboiled detective
2. Sam Spade
3. 1930s mystery
4. classic detective fiction
5. noir fiction
6. public domain audiobook
7. Dashiell Hammett

### ISBN/ASIN
- Generate ASIN through platform upload
- Consider purchasing ISBN for wider distribution

---

## Cover Art Guidelines

### Style Direction
- Art Deco aesthetic (1930s)
- Color palette: Black, gold, deep red, cream
- Typography: Period-appropriate sans-serif or art deco fonts
- Central element: Falcon silhouette (NOT the movie prop)

### Required Elements
- Title: "The Maltese Falcon"
- Author: "Dashiell Hammett"
- Format indicator: "AUDIOBOOK" or speaker icon
- DO NOT include: Film imagery, Bogart, movie references

### Cover Art Prompt (for AI generation)
```
Art deco book cover design for "The Maltese Falcon" by Dashiell Hammett.
1930s San Francisco noir aesthetic. Central motif: stylized black falcon
silhouette on golden geometric art deco background. Typography in period
art deco style. Color palette: black, gold, deep red, cream. No human
faces. Vintage detective novel style.
```

### Dimensions
- Findaway: 2400x2400px minimum (square)
- Google Play: 1600x2400px minimum
- General: 3000x3000px recommended for flexibility

---

## Platform-Specific Settings

### Findaway Voices
- **Price**: $9.99 (competitive for classic)
- **Distribution**: All retailers EXCEPT Audible
- **Sample Length**: 5 minutes
- **Release Type**: Full catalog

### Google Play Books
- **Price**: $7.99 (Google audience is price-sensitive)
- **Distribution**: Google Play only
- **Exclusive Period**: None
- **Auto-price**: Disabled

### Direct Sales (Gumroad/Payhip)
- **Price**: $4.99 (lower price, higher margin)
- **Bundle Option**: Include PDF of original text
- **Discount Codes**: LAUNCH20 for 20% off first month

---

## Revenue Projections

### Conservative Estimate (Month 1-6)
| Platform | Units/Month | Price | Royalty | Monthly |
|----------|-------------|-------|---------|---------|
| Findaway | 15 | $9.99 | 70% | $105 |
| Google Play | 25 | $7.99 | 70% | $140 |
| Direct | 10 | $4.99 | 95% | $47 |
| **Total** | **50** | | | **$292** |

### Realistic Estimate (Month 7-12)
| Platform | Units/Month | Price | Royalty | Monthly |
|----------|-------------|-------|---------|---------|
| Findaway | 30 | $9.99 | 70% | $210 |
| Google Play | 50 | $7.99 | 70% | $280 |
| Direct | 20 | $4.99 | 95% | $95 |
| **Total** | **100** | | | **$585** |

---

## Production Timeline

| Day | Task | Duration |
|-----|------|----------|
| 1 | Download source, run cleanup | 2 hours |
| 2 | Voice profile setup, test synthesis | 2 hours |
| 3 | Full TTS synthesis (automated) | 4-6 hours (GPU) |
| 4 | QA pass - listen to samples | 2 hours |
| 5 | Audio mastering (automated) | 2-3 hours |
| 6 | Cover art generation | 1 hour |
| 7 | Metadata prep, upload to platforms | 2 hours |

**Total Active Time**: ~15-18 hours
**Total Elapsed Time**: ~7 days

---

## Files Generated

After production, expect these files:
```
output/maltese_falcon/
├── raw/
│   ├── chapter_01.wav
│   ├── chapter_02.wav
│   └── ... (20 chapters)
├── mastered/
│   ├── chapter_01.wav
│   ├── chapter_02.wav
│   └── ... (20 chapters)
├── final/
│   ├── maltese_falcon_2026.mp3
│   └── maltese_falcon_2026.m4b
├── metadata/
│   ├── findaway_metadata.json
│   ├── google_play_metadata.json
│   └── retail_description.md
└── assets/
    ├── cover_3000x3000.jpg
    ├── cover_2400x2400.jpg
    └── cover_1600x2400.jpg
```

---

## Risk Assessment

| Risk | Probability | Mitigation |
|------|-------------|------------|
| Voice quality issues | Medium | Test extensively, have backup voice |
| Pronunciation errors | Medium | Pre-mark difficult words, manual review |
| Platform rejection | Low | Follow guidelines, document PD status |
| Copyright claim | Very Low | Have PD documentation ready |
| Low sales | Medium | Marketing plan, patience |

---

## Notes & Reminders

1. **EU Distribution**: Block EU territories until 2032 (Hammett died 1961)
2. **Film References**: NEVER mention the 1941 film in descriptions
3. **Character Usage**: Sam Spade is free to use per 1954 court ruling
4. **Quality Bar**: This is launch title - extra QA attention required
5. **Evidence**: Screenshot all uploads for dispute response file
