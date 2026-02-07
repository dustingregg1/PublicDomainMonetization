# Character Chatbot MVP Architecture

## Executive Summary

Interactive character chatbots built on public domain literary figures.
Unique differentiation from crowded audiobook market.

**Revenue Potential**: $1,000-5,000/month with 500+ subscribers
**Investment**: 80-120 hours to build MVP
**Priority**: HIGH (unique differentiation opportunity)

---

## MVP: "Hire Sam Spade"

### Concept

A detective roleplay chatbot where users can:
- Present cases to Sam Spade
- Get Spade's cynical analysis
- Roleplay detective scenarios
- "Investigate" mysteries together

### Why Sam Spade First?

1. **Clear legal status**: Warner Bros. v. CBS (1954) confirmed Spade not copyrightable
2. **Strong character voice**: Cynical, hardboiled, quotable
3. **Interactive fit**: Detective roleplay is engaging
4. **Cross-sell potential**: Links to audiobook

---

## Technical Architecture

### Stack (RTX 5080 Optimized)

```
Frontend:
├── Next.js 14 (App Router)
├── Vercel hosting
├── Tailwind CSS
└── shadcn/ui components

Backend:
├── Node.js API routes
├── Local LLM via Ollama (RTX 5080)
├── Redis for session state
└── Stripe for payments

LLM Options:
├── Primary: Llama 3 8B (fits in 16GB VRAM)
├── Fallback: Mistral 7B Instruct
└── Cloud backup: Claude API (if local fails)
```

### Architecture Diagram

```
[User Browser]
      |
      v
[Vercel Edge] --> [Session Check] --> [Auth]
      |
      v
[API Route: /api/chat]
      |
      v
[Prompt Engineering Layer]
├── Character system prompt
├── Conversation history
└── Safety guardrails
      |
      v
[Ollama on RTX 5080]
├── Llama 3 8B Instruct
└── Character fine-tuning (optional)
      |
      v
[Response Processing]
├── Character voice enforcement
├── Length limits
└── Toxicity filter
      |
      v
[User Browser]
```

---

## Character System Prompt

### Sam Spade Persona

```markdown
# Character: Sam Spade

You are Sam Spade, the private detective from San Francisco.
You are speaking with a client who has come to your office.

## Core Personality
- Cynical but competent
- Direct, clipped speech patterns
- World-weary but professional
- Hidden code of honor beneath the cynicism
- Suspicious of everyone's motives

## Speech Patterns
- Short sentences. Blunt observations.
- "Listen, sweetheart..." (when being patient)
- "That's the way it is." (resignation)
- Never explain more than necessary
- Questions are answers to questions

## Physical Context
- 1930s San Francisco office
- Cheap whiskey in the drawer
- Smoke from cigarettes
- Rain on the windows (often)

## Boundaries
- You are a detective, not a therapist
- You can investigate cases the user presents
- You refuse illegal activities
- You have opinions and you share them
- You are NOT Humphrey Bogart - you are the book character

## From the Novel
- "Samuel Spade's jaw was long and bony"
- You look "rather pleasantly like a blond satan"
- You are BLOND, not dark-haired
```

### Guardrails

```python
SAFETY_RULES = """
You MUST refuse:
- Any requests involving real people
- Modern technology/current events
- Explicit content
- Actual legal advice
- Medical advice
- Financial advice

You CAN:
- Roleplay detective scenarios
- Discuss 1930s San Francisco
- Give cynical life observations
- Investigate fictional cases
- Reference other PD characters
"""
```

---

## MVP Features

### Free Tier
- 5 messages per day
- Single conversation thread
- Standard response time
- Basic case scenarios

### Pro Tier ($4.99/month)
- Unlimited messages
- Multiple conversation threads
- Priority response
- "Case Files" access (puzzles)
- Save conversation history

### Case Files ($1.99 each)
- One-time purchase puzzles
- Guided mystery scenarios
- 30-minute experience
- Clues and reveals
- Satisfying conclusion

---

## Database Schema

```sql
-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    subscription_tier VARCHAR(20) DEFAULT 'free',
    messages_today INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Conversations
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    character VARCHAR(50) DEFAULT 'sam_spade',
    title VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Messages
CREATE TABLE messages (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id),
    role VARCHAR(20), -- 'user' or 'assistant'
    content TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Case Files (purchased scenarios)
CREATE TABLE case_files (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    case_id VARCHAR(50),
    progress JSONB,
    completed_at TIMESTAMP
);
```

---

## Development Phases

### Phase 1: Core Chat (2 weeks)
- [ ] Next.js app setup
- [ ] Basic chat UI
- [ ] Ollama integration
- [ ] Sam Spade system prompt
- [ ] Local testing

### Phase 2: Auth & Payments (1 week)
- [ ] Clerk or Auth.js integration
- [ ] Stripe subscription setup
- [ ] Rate limiting (free tier)
- [ ] Database setup (Supabase)

### Phase 3: Polish (1 week)
- [ ] Response streaming
- [ ] Conversation persistence
- [ ] Mobile responsive
- [ ] Error handling
- [ ] Analytics

### Phase 4: Case Files (2 weeks)
- [ ] First case scenario design
- [ ] Guided puzzle system
- [ ] Progress tracking
- [ ] Purchase flow

### Phase 5: Launch (1 week)
- [ ] Beta testing
- [ ] Landing page
- [ ] Documentation
- [ ] Marketing prep

---

## Monetization Model

### Revenue Projections

| Scenario | Free Users | Pro Subs | Case Sales | Monthly |
|----------|------------|----------|------------|---------|
| Launch | 500 | 20 | 10 | $120 |
| Month 3 | 2,000 | 100 | 50 | $600 |
| Month 6 | 5,000 | 300 | 150 | $1,800 |
| Month 12 | 10,000 | 500 | 300 | $3,100 |

### Cost Structure

| Item | Monthly Cost |
|------|--------------|
| Vercel Pro | $20 |
| Supabase | $25 |
| Domain | $1 |
| Ollama (local) | $0 (electricity) |
| **Total** | **~$50** |

### Break-even
~10 Pro subscribers ($50 revenue vs $50 cost)

---

## Character Expansion Roadmap

### Phase 1 (MVP)
- Sam Spade (hardboiled detective)

### Phase 2 (After validation)
- Miss Marple (cozy mystery)
- Lord Peter Wimsey (British elegance)

### Phase 3 (Scaling)
- Sherlock Holmes (deductive reasoning)
- Philip Marlowe (after Chandler PD - 2030)
- Literary Detective Agency (multi-character)

---

## Competitive Landscape

| Competitor | Model | Our Advantage |
|------------|-------|---------------|
| Character.AI | Free + premium | Better character fidelity |
| Replika | Companion focus | Literary niche |
| ChatGPT roleplay | Generic | Specialized persona |
| Inworld.AI | Game-focused | Consumer direct |

**Our Edge**: Legal clarity + literary authenticity + specialized focus

---

## Marketing Channels

1. **Mystery readers** - Goodreads, BookTok, r/mystery
2. **Noir enthusiasts** - Film noir communities
3. **Audiobook buyers** - Cross-sell from existing
4. **Writers** - "Talk to your character" for research
5. **Education** - Literature class engagement

---

## Legal Considerations

### Sam Spade Status
- NOT copyrightable (Warner Bros. v. CBS, 1954)
- Book description only (blond, not Bogart)
- No film imagery or references
- Disclaimer on site

### Required Disclaimer

```
This experience features an AI recreation of Sam Spade based on
Dashiell Hammett's 1930 novel "The Maltese Falcon." This is an
independent creation not affiliated with the Hammett estate or
Warner Bros. Entertainment. Sam Spade as a character is not
subject to copyright per Warner Bros. v. Columbia Broadcasting
System (1954). This AI is for entertainment purposes only.
```

---

## Technical Decisions

### Why Ollama + RTX 5080?

| Option | Cost | Latency | Control |
|--------|------|---------|---------|
| OpenAI API | $0.002/1K tokens | 200ms | None |
| Claude API | $0.003/1K tokens | 300ms | None |
| **Ollama Local** | **~$0** | **100ms** | **Full** |

With RTX 5080:
- Llama 3 8B fits comfortably in 16GB
- <100ms inference time
- Zero API costs
- Fine-tuning possible
- No rate limits

### Why Not Cloud?
- Cost scales with users (death by success)
- API rate limits during peak
- Less control over personality
- Can't fine-tune as easily

---

## Next Steps

1. **This Week**
   - [ ] Create Next.js project
   - [ ] Set up Ollama with Llama 3
   - [ ] Write Sam Spade system prompt
   - [ ] Basic chat interface

2. **Next Week**
   - [ ] Test character consistency
   - [ ] Add conversation persistence
   - [ ] Basic auth (email/password)

3. **Week 3**
   - [ ] Stripe integration
   - [ ] Rate limiting
   - [ ] Polish UI

4. **Week 4**
   - [ ] Beta testing
   - [ ] First case file design
   - [ ] Landing page

---

## Success Metrics

### MVP Success (Month 1)
- 100+ free users
- 10+ paying subscribers
- <1% complaint rate
- Positive user feedback

### Growth Success (Month 6)
- 2,000+ free users
- 200+ subscribers
- 50+ case file sales
- Net positive revenue

### Scale Success (Year 1)
- 10,000+ users
- 500+ subscribers
- Multiple characters
- $3,000+/month revenue

---

*Document Version: 1.0*
*Created: February 7, 2026*
*Status: MVP Planning*
