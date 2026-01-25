# Public Domain Monetization Agent Swarm Architecture

## Overview

This document defines the specialized agent swarm for automated public domain content monetization. The system uses a hierarchical orchestration model where specialized sub-agents hunt and gather information, then synthesize it into actionable monetization outputs.

---

## Agent Hierarchy

```
                    ┌─────────────────────────────────────┐
                    │      MASTER ORCHESTRATOR            │
                    │   (Coordination & Synthesis)        │
                    └──────────────┬──────────────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
┌───────▼───────┐        ┌────────▼────────┐        ┌────────▼────────┐
│   RESEARCH    │        │   PRODUCTION    │        │  MONETIZATION   │
│    SWARM      │        │     SWARM       │        │     SWARM       │
└───────┬───────┘        └────────┬────────┘        └────────┬────────┘
        │                         │                          │
   ┌────┴────┐              ┌─────┴─────┐              ┌─────┴─────┐
   │         │              │           │              │           │
┌──▼──┐  ┌───▼───┐     ┌────▼────┐ ┌────▼────┐   ┌────▼────┐ ┌────▼────┐
│PD   │  │Legal  │     │Content  │ │Format   │   │KDP      │ │Revenue  │
│Scout│  │Clear. │     │Creator  │ │Expert   │   │Optimizer│ │Tracker  │
└─────┘  └───────┘     └─────────┘ └─────────┘   └─────────┘ └─────────┘
```

---

## Research Swarm (Hunt & Gather)

### 1. PD Scout Agent
**Purpose:** Continuously discover and evaluate public domain opportunities

**Capabilities:**
- Monitor Duke Law, Internet Archive, Project Gutenberg for new PD entries
- Evaluate market potential using Amazon BSR analysis
- Track competitor annotated editions
- Identify underserved niches

**Triggers:**
- New calendar year (January 1)
- Weekly market scans
- User queries about specific works

**Outputs:**
- Tier 1/2/3 work classifications
- Market opportunity scores
- Competitor analysis reports

### 2. Legal Clearance Agent
**Purpose:** Verify PD status and trademark clearance

**Capabilities:**
- USPTO trademark database searches
- EU copyright term calculations
- Enforcement history research
- Platform-specific risk assessment

**Tools Used:**
- USPTO TESS search
- EU copyright databases
- Legal precedent databases
- Platform TOS analysis

**Outputs:**
- PD Dossiers with clearance status
- Risk matrices
- Dispute response templates

### 3. Source Hunter Agent
**Purpose:** Locate and verify authentic source editions

**Capabilities:**
- Internet Archive deep search
- HathiTrust verification
- Library of Congress cross-reference
- Edition comparison analysis

**Outputs:**
- Verified source URLs
- Edition verification reports
- Source text downloads

### 4. Market Intelligence Agent
**Purpose:** Gather competitive and market data

**Capabilities:**
- Amazon category analysis
- Keyword opportunity research
- Pricing optimization
- Review sentiment analysis

**Tools Used:**
- Amazon Product API (via scraping fallback)
- Publisher Rocket data extraction
- Google Trends analysis
- Goodreads API

**Outputs:**
- Market reports
- Keyword recommendations
- Pricing strategies

---

## Production Swarm (Create & Format)

### 5. Content Creator Agent
**Purpose:** Generate high-quality companion content

**Capabilities:**
- Introduction writing with historical context
- Chapter-by-chapter summaries
- Character guides with analysis
- Discussion questions for book clubs
- Glossaries of period terms
- Edition comparison essays

**Quality Gates:**
- Fact verification against source
- Quote authenticity checking
- Plagiarism scanning
- Style consistency

**Outputs:**
- Complete manuscript sections
- AI draft with human QA markers
- Word count verification

### 6. Format Expert Agent
**Purpose:** Professional formatting for all platforms

**Capabilities:**
- Ebook formatting (EPUB, MOBI)
- Print formatting (PDF)
- Atticus/Vellum automation
- KDP spec compliance

**Platform Specs:**
- Kindle: EPUB 2.0/3.0
- Print: PDF/X-1a with bleed
- Cover: 2560x1600 (ebook), dynamic spine (print)

**Outputs:**
- Publication-ready files
- Cover specifications
- Format compliance reports

### 7. Cover Design Agent
**Purpose:** Generate on-brand cover designs

**Capabilities:**
- Genre-appropriate design generation
- Series branding consistency
- Trademark-safe imagery selection
- Multi-format adaptation

**Design Guidelines:**
- Art Deco noir for detective fiction
- Academic elegance for literary fiction
- Cosmic imagery for science fiction
- Period-appropriate typography

**Outputs:**
- Cover mockups
- Canva template specifications
- Image asset requirements

---

## Monetization Swarm (Publish & Optimize)

### 8. KDP Optimizer Agent
**Purpose:** Maximize KDP listing performance

**Capabilities:**
- Metadata optimization
- Category selection strategy
- Keyword research and placement
- Pricing A/B testing
- Review acquisition strategy

**Compliance Focus:**
- PD content requirements
- Originality statements
- Differentiation documentation

**Outputs:**
- Complete KDP listing kits
- Keyword matrices
- Pricing recommendations

### 9. Revenue Tracker Agent
**Purpose:** Monitor and optimize revenue streams

**Capabilities:**
- Sales data aggregation
- ROI analysis per title
- Trend identification
- Opportunity flagging

**Metrics Tracked:**
- Revenue per title
- KENP reads
- Conversion rates
- Review velocity

**Outputs:**
- Revenue dashboards
- Optimization recommendations
- Expansion opportunities

### 10. Dispute Response Agent
**Purpose:** Handle platform issues and legal challenges

**Capabilities:**
- Automated dispute documentation
- Response template generation
- Evidence packet assembly
- Escalation protocols

**Response Types:**
- KDP suppression appeals
- Trademark complaints
- DMCA counter-notifications
- Platform policy clarifications

**Outputs:**
- Dispute response drafts
- Evidence packages
- Resolution tracking

---

## Orchestration Protocols

### Workflow: New Title Discovery to Publication

```
1. TRIGGER: Market Intelligence Agent identifies opportunity
   └─> PD Scout Agent verifies PD status
       └─> Legal Clearance Agent performs clearance
           └─> IF CLEAR:
               └─> Source Hunter Agent locates source
                   └─> Content Creator Agent generates content
                       └─> Format Expert Agent produces files
                           └─> Cover Design Agent creates cover
                               └─> KDP Optimizer Agent creates listing
                                   └─> PUBLISH
               └─> IF NOT CLEAR:
                   └─> Flag for manual review
                   └─> Add to "Verification Required" list
```

### Parallel Processing Rules

| Phase | Can Run in Parallel | Dependencies |
|-------|---------------------|--------------|
| Research | All research agents | None |
| Clearance | After PD status confirmed | PD Scout output |
| Content | After source located | Source Hunter output |
| Production | After content approved | Content Creator output |
| Publishing | After all production complete | All production outputs |

### Error Handling

| Error Type | Response | Escalation |
|------------|----------|------------|
| PD status unclear | Flag for manual review | Legal Clearance Agent |
| Source not found | Try alternative archives | Source Hunter Agent |
| Content quality below threshold | Regenerate with different prompt | Content Creator Agent |
| KDP rejection | Deploy Dispute Response Agent | Immediate |
| Trademark complaint | Assemble evidence, respond within 48h | Dispute Response Agent |

---

## API & Tool Integration

### External APIs

| Service | Purpose | Agent(s) |
|---------|---------|----------|
| Internet Archive | Source texts | Source Hunter |
| USPTO TESS | Trademark search | Legal Clearance |
| Google Trends | Market trends | Market Intelligence |
| Amazon PA API | Product data | Market Intelligence, KDP Optimizer |
| OpenAI/Anthropic | Content generation | Content Creator |

### MCP Tools Available

| Tool | Purpose |
|------|---------|
| WebSearch | Research and discovery |
| WebFetch | Archive access |
| Context7 | Documentation lookup |
| Playwright | Browser automation |
| Memory | Context persistence |
| Reddit | Community research |
| PDF Tools | Document processing |

### Internal Tools

| Tool | Purpose |
|------|---------|
| cleanup_text.py | OCR text cleanup |
| verify_deployment.py | Pre-publish verification |

---

## Agent Configuration Files

Each agent has a configuration file in `~/.claude/agents/pd-<agent-name>.md` that defines:

1. Role and responsibilities
2. Available tools
3. Quality thresholds
4. Output formats
5. Escalation triggers

---

## Continuous Improvement

### Learning Loops

1. **Success Patterns**: Track what works (keywords, pricing, covers)
2. **Failure Analysis**: Document rejections and disputes
3. **Market Evolution**: Update strategies based on market changes
4. **Tool Updates**: Integrate new tools as they become available

### Metrics for Optimization

| Metric | Target | Action if Below |
|--------|--------|-----------------|
| Title production time | <12 hours | Streamline bottlenecks |
| KDP approval rate | >95% | Improve compliance |
| Revenue per title (6mo) | >$500 | Improve marketing |
| Dispute win rate | >90% | Strengthen documentation |

---

## Implementation Status

| Agent | Status | Priority |
|-------|--------|----------|
| Master Orchestrator | Active | P0 |
| PD Scout | In Development | P1 |
| Legal Clearance | In Development | P1 |
| Source Hunter | In Development | P1 |
| Market Intelligence | Planned | P2 |
| Content Creator | Active | P0 |
| Format Expert | Planned | P2 |
| Cover Design | Planned | P2 |
| KDP Optimizer | In Development | P1 |
| Revenue Tracker | Planned | P3 |
| Dispute Response | In Development | P1 |

---

*Last Updated: January 24, 2026*
