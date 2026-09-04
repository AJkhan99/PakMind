# PakMind — Pakistan's AI Knowledge Platform

---

## The Problem

**220 million Pakistanis** face a daily information gap:

- Government service procedures (passport, CNIC, domicile, driving licence) are scattered across dozens of websites, mostly in English
- Policy updates, tax changes, and new notifications are published in gazettes and PDFs that citizens never see
- Scholarship opportunities worth **billions of rupees** go unclaimed every year because students don't know they're eligible
- Most citizens cannot navigate these systems in their own language — **Urdu** or **Roman Urdu**

**The result?** A student in rural Punjab misses a fully-funded HEC scholarship. A shopkeeper in Karachi doesn't know the new tax rate applies to him. A mother in Peshawar doesn't know the domicile process changed last month.

---

## The Solution: PakMind

**One platform. Three AI modules. Three languages. Zero cost to the user.**

PakMind is an AI-powered knowledge platform that makes Pakistani government information, policy updates, and scholarship opportunities accessible to every citizen — in the language they speak.

```
PakMind
├── PakGuide   → "How do I get a passport?" (Government Services)
├── PakWatch   → "What changed in the new budget?" (Policy Updates)
└── PakScholar → "Which scholarships am I eligible for?" (Scholarship Matching)
```

---

## Module 1: PakGuide — Government Services AI

**"Your personal guide to every government service in Pakistan"**

### What it does
Answers questions about **17+ government services** with verified, structured information:
- Passport (new, renewal, NICOP)
- CNIC / SNICOP
- Domicile certificate
- Driving licence (learner, permanent, international)
- Birth / Death / Marriage certificates
- Police character certificate
- Vehicle registration
- Arms licence
- Tax filing (NTN, FBR returns)
- Land records (fard, inteqal)
- Utility connections
- Government jobs (CSS, PMS)
- Pension & EOBI

### How it works — 5-Phase Intelligent Retrieval Pipeline

```
User Query
    │
    ▼
Phase 1: Heuristic Query Parsing (~0ms)
    → Detects: service, province, city, intent, language
    → No LLM call — pure pattern matching (400-line heuristic engine)
    │
    ▼
Phase 2: Parallel Multi-Source Search (~2-3s)
    → Vector search (pgvector cosine similarity on document chunks)
    → Keyword search (ILIKE on government_services table)
    → Structured search (by service name + province + city)
    → Web search (Serper.dev + DuckDuckGo fallback)
    → YouTube search (official gov tutorials)
    All 5 searches run simultaneously via ThreadPoolExecutor
    │
    ▼
Phase 3: Context Strength Assessment
    → Scores DB results (vector + keyword combined ranking)
    → Determines if DB context is "strong" or "weak"
    │
    ▼
Phase 4: Deep Scraping Fallback (~3-5s, only if DB is weak)
    → Scrapes known government websites LIVE (dgip.gov.pk, nadra.gov.pk, etc.)
    → Deep-scrapes top web search results (full page content extraction)
    → Prioritizes .gov.pk domains as "trusted sources"
    │
    ▼
Phase 5: AI Answer Generation + Verification
    → Primary LLM generates structured answer (Google Gemini — FREE)
    → Secondary LLM cross-verifies the answer (Groq Llama — FREE)
    → Auto-adjusts confidence based on actual source quality
    → Auto-enriches DB (learns from web answers for future queries)
```

### Key Features
- **Structured answers**: Requirements, Steps, Fee, Processing Time, Application URL, Contact Info, Eligibility
- **AI Verification**: Every answer is cross-checked by a second LLM before display
- **Auto-enrichment**: When the DB lacks info, PakGuide scrapes the web, answers the question, and *stores the answer in the DB* for next time
- **PDF Checklist**: Download a printable checklist with fee calculator
- **Office Locator**: Find the nearest government office
- **Voice Input**: Ask in English or Urdu using your voice
- **YouTube Tutorials**: Linked official video guides when available
- **Source Citations**: Every answer cites its sources (DB, gov website, or web search)

---

## Module 2: PakWatch — Government Updates Monitor

**"Never miss a policy change that affects you"**

### What it does
Tracks and explains **Pakistani government updates** in real-time:
- Petrol & gas price changes
- Tax rate modifications
- New notifications & circulars
- Budget announcements
- Minimum wage updates
- Interest rate decisions (SBP)
- Regulatory changes
- New schemes & programs

### How it works — 3-Way RAG Pipeline

```
User Query
    │
    ▼
Phase 1: Query Understanding
    → Extracts: category, province, importance level, time range
    │
    ▼
Phase 2: Triple Retrieval
    → Vector search on government_updates (semantic matching)
    → Keyword search (multi-field ILIKE)
    → Structured filter search (by category/province/importance)
    │
    ▼
Phase 3: AI Answer + Web Fallback
    → If DB has the answer → generate from verified data
    → If DB doesn't have it → Gemini grounded search (google_search tool)
    → Caches web answers for 7 days (TTL-based, similarity dedup)
    │
    ▼
Phase 4: Verification + Citation
    → Cross-checks answer against source context
    → Builds citations with trust levels
```

### Key Features
- **Hot Topic Digests**: Pre-computed summaries of trending topics (petrol prices, tax changes)
- **Importance Ranking**: Updates tagged as Critical / High / Medium / Low
- **Category Filtering**: Browse by category (Economy, Education, Health, etc.)
- **Province Filtering**: Filter updates by province
- **Web Answer Cache**: Out-of-DB questions answered via Gemini's grounded Google Search, cached for 7 days
- **What Changed / Who's Affected**: Every answer highlights what changed and who it impacts
- **Live Updates**: Real-time monitoring of government notifications

---

## Module 3: PakScholar — AI Scholarship Matcher

**"Tell us about yourself. We'll find the scholarships."**

### What it does
Matches Pakistani students with scholarships, grants, and internships they are **actually eligible for**:
- HEC scholarships (need-based, merit-based)
- Fulbright, Chevening, Erasmus Mundus
- PEEF, SEEF, BEEF, CMEEF provincial scholarships
- University-specific financial aid
- International study opportunities
- Internship programs

### How it works — Two-Phase Eligibility Matching

```
User Profile: "I'm a BS Computer Science student from Punjab with 3.5 CGPA, female"
    │
    ▼
Phase 1: Database Matching
    → Fetches ALL opportunities from verified database
    → AI evaluates each opportunity against user profile
    → Returns: eligible ✓, maybe ⚠️, or not eligible ✗
    → Each match includes reasoning ("You're eligible because...")
    │
    ▼
Phase 2: Web Search Fallback (only if Phase 1 finds no eligible matches)
    → Serper.dev Google search for current scholarships
    → AI evaluates web results for relevance
    → Clearly labeled as "unverified — please check"
    │
    ▼
Output:
    → database_matches[] — verified, with eligibility verdict
    → web_matches[] — current opportunities from the web
    → answer_summary — personalized recommendation
```

### Key Features
- **Tri-state Eligibility**: Eligible / Maybe / Not Eligible (not just yes/no)
- **Personalized Reasoning**: Each match explains WHY you're eligible or not
- **Urdu Support**: Full responses in Urdu script when queried in Urdu
- **Deadline Awareness**: Shows application deadlines prominently
- **Direct Apply Links**: One-click links to application portals
- **Database + Web**: Verified DB first, live web search as fallback

---

## What Makes PakMind Unique

### 1. **Pakistan-First, Not Adapted**
Most AI tools are generic — trained on Western data, in English only. PakMind is built *from scratch* for Pakistan:
- Knows that "domisile" = "domicile" (Roman Urdu spelling variations)
- Understands "shanakhti card" = "CNIC"
- Handles Urdu script (اردو), Roman Urdu (Urdu in English letters), AND English — all in the same query

### 2. **Trilingual by Design**
Not "translated" — natively trilingual:
- **English**: "How do I get a passport?"
- **Roman Urdu**: "Passport kaise banwayen?"
- **Urdu Script**: "پاسپورٹ کیسے بنوائیں؟"
- All three produce the same quality answer, in the user's language

### 3. **AI Verification Layer**
Every answer passes through TWO independent LLMs:
- Primary LLM generates the answer
- Secondary LLM (different provider) verifies it against the source data
- If they disagree, warnings are shown to the user
- This dramatically reduces hallucinations

### 4. **Self-Learning System**
PakGuide auto-enriches its database:
- When the DB lacks information but the web has it, PakGuide answers from the web
- It then *stores that answer back into the database*
- Next time someone asks the same question, it answers from DB instantly
- The system gets smarter with every query

### 5. **100% Free to Run**
The entire stack runs on free-tier APIs:
- Google Gemini (free) — primary LLM + embeddings
- Groq Llama (free) — verification LLM
- Supabase (free) — database + vector search
- Serper.dev (free) — web search
- DuckDuckGo (free) — backup search
- **Zero paid API costs** for the operator

### 6. **Deep Government Scraping**
Unlike ChatGPT or generic AI tools that hallucinate government procedures:
- PakGuide has a curated database of verified Pakistani government services
- When the DB is insufficient, it scrapes the **actual government websites** live (dgip.gov.pk, nadra.gov.pk, etc.)
- Answers are grounded in real, official content — not AI guesses

### 7. **Smart Intent Routing**
The landing page doesn't make users choose a module:
- Type any question → PakMind automatically detects which module should handle it
- Keyword scoring across 3 languages determines the best module
- "Passport" → PakGuide, "Petrol price" → PakWatch, "Scholarship" → PakScholar

---

## Technology Stack

### Frontend
| Layer | Technology |
|-------|-----------|
| Framework | Next.js 16 (App Router) |
| UI Library | React 19 |
| Styling | Tailwind CSS 4 (CSS-only @theme) |
| Animations | Framer Motion |
| Icons | React Icons (Heroicons) |
| Fonts | Poppins (Latin) + Noto Nastaliq Urdu |
| Language | TypeScript 5 |
| Build | Turbopack |

### Backend
| Layer | Technology |
|-------|-----------|
| Framework | FastAPI (Python) |
| Validation | Pydantic v2 + pydantic-settings |
| Database | Supabase (PostgreSQL) |
| Vector Search | pgvector (1536-dim embeddings) |
| Primary LLM | Google Gemini (REST API, free tier) |
| Verification LLM | Groq Llama (OpenAI-compatible, free tier) |
| Fallback LLM | OpenAI (optional, paid) |
| Embeddings | Google gemini-embedding-001 (1536-dim, free) |
| Web Search | Serper.dev + DuckDuckGo |
| Grounded Search | Gemini google_search tool |
| PDF Generation | fpdf2 |
| Web Scraping | BeautifulSoup4 + lxml + httpx |
| Server | Uvicorn (ASGI) |

### Architecture
| Component | Design |
|-----------|--------|
| Process Count | 2 (1 frontend + 1 backend) |
| Frontend Routes | `/` (landing), `/guide`, `/watch`, `/scholar` |
| Backend Routers | `/api/guide/*`, `/api/watch/*`, `/api/scholar/*`, `/api/feedback/*` |
| Domain Isolation | Separate Python packages (app.guide, app.watch, app.scholar) |
| Shared Infrastructure | Unified config, DB layer, AI router, embeddings |
| Security | CORS, rate limiting (20 req/min), request size limits, security headers |
| Key Rotation | Dual Google API keys with automatic 429 failover |
| LLM Fallback Chain | Google → Groq → OpenAI (automatic) |

### Theme: PakDark Glass
- Background: `#0a1a0f` (deep green-black)
- Cards: Glassmorphism (`rgba(255,255,255,0.05)` + `backdrop-blur: 16px`)
- Gradient text: `#00c853` → `#14b8a6` → `#10b981` (Pakistan green to teal)
- Animated floating blobs in the background
- Glowing input focus states
- Module-specific accent colors

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    PakMind Frontend                          │
│                  (Next.js 16 — Port 3000)                    │
│                                                             │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
│   │ Landing  │  │ PakGuide │  │ PakWatch │  │ PakScholar│  │
│   │ Page /   │  │ /guide   │  │ /watch   │  │ /scholar  │  │
│   │          │  │          │  │          │  │           │  │
│   │ Smart    │  │ Chat     │  │ Filters  │  │ Profile   │  │
│   │ Search   │  │ Voice    │  │ Hot      │  │ Matches   │  │
│   │ Module   │  │ PDF      │  │ Topics   │  │ Web       │  │
│   │ Cards    │  │ Feedback │  │ Latest   │  │ Results   │  │
│   └─────┬────┘  └────┬─────┘  └────┬─────┘  └─────┬─────┘  │
│         │             │             │              │         │
│         └─────────────┴──────┬──────┴──────────────┘         │
│                              │                               │
│                    Single API Client                         │
│                  (NEXT_PUBLIC_API_URL)                       │
└──────────────────────────────┬───────────────────────────────┘
                               │ HTTP (JSON)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   PakMind Backend                            │
│                  (FastAPI — Port 8000)                       │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐   │
│   │              Security Layer                          │   │
│   │  CORS │ Rate Limiter │ Size Limit │ Security Headers │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                             │
│   ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐  │
│   │ /api/guide│ │ /api/watch│ │/api/scholar│ │/api/feedback│ │
│   │           │ │           │ │           │ │             │  │
│   │ 5-phase   │ │ 3-way     │ │ 2-phase   │ │ Submit      │  │
│   │ retrieval │ │ retrieval │ │ matching  │ │ Stats       │  │
│   │ deep      │ │ grounded  │ │ Serper    │ │ PDF         │  │
│   │ scraping  │ │ search    │ │ fallback  │ │ Refresh     │  │
│   └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └─────────────┘  │
│         │             │             │                        │
│   ┌─────┴─────────────┴─────────────┴─────┐                  │
│   │         Shared AI Layer                │                  │
│   │                                        │                  │
│   │  call_llm_json()                       │                  │
│   │  ┌──────────┐ ┌──────┐ ┌────────┐     │                  │
│   │  │ Google   │→│ Groq │→│ OpenAI │     │                  │
│   │  │ Gemini   │ │Llama ││ (paid) │     │                  │
│   │  │ (FREE)   │ │(FREE)││        │     │                  │
│   │  └──────────┘ └──────┘ └────────┘     │                  │
│   │                                        │                  │
│   │  embed_text() — Google gemini-embedding │                  │
│   │  call_google_grounded() — web search    │                  │
│   │  Dual API key rotation on 429           │                  │
│   └──────────────────────────────────────────┘                  │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐   │
│   │              Supabase (PostgreSQL)                    │   │
│   │                                                      │   │
│   │  government_services │ government_updates │ opportunities │
│   │  document_chunks (pgvector) │ sources │ documents    │   │
│   │  topic_digests │ web_answers (7-day cache)           │   │
│   └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Who It Helps

| User | Problem | PakMind Solution |
|------|---------|-----------------|
| **Rural student** | Doesn't know which scholarships they qualify for | PakScholar matches profile against all opportunities, responds in Urdu |
| **Small business owner** | Missed a tax notification that affects their filing | PakWatch monitors all updates, explains what changed and who's affected |
| **First-time passport applicant** | Confused by the process, doesn't speak English | PakGuide gives step-by-step instructions in Roman Urdu with fee breakdown |
| **Government employee** | Needs to know new pension rules | PakWatch finds the exact notification, AI summarizes it in plain language |
| **Parent** | Child's domicile application was rejected — wants to know the correct process | PakGuide provides verified requirements with downloadable checklist |
| **University student** | Looking for international study opportunities | PakScholar searches both verified DB and live web for current openings |
| **Journalist / Researcher** | Needs accurate government data | PakWatch provides sourced, verified updates with direct links to official documents |

---

## Demo Flow (For Hackathon Presentation)

### Opening (30 seconds)
> "In Pakistan, 220 million people struggle to access basic government information. Today, I'm showing you PakMind — an AI platform that makes this information accessible in English, Roman Urdu, and Urdu script. And it costs nothing to run."

### Demo 1: PakGuide — Smart Government Assistant (2 minutes)
1. **Open landing page** → Show the PakDark Glass theme
2. **Type in Roman Urdu**: *"passport kaise banwayen?"*
3. Smart search auto-routes to PakGuide
4. **Show the structured answer**: requirements, steps, fee, processing time
5. **Show source citations** and confidence badge
6. **Click "Download PDF"** → printable checklist
7. **Show voice input** → speak a question in English

### Demo 2: PakWatch — Policy Monitor (2 minutes)
1. **Navigate to /watch**
2. **Ask**: *"What is the current petrol price in Pakistan?"*
3. Show the grounded web search answer with sources
4. **Show Hot Topics** section — pre-computed digests
5. **Apply filters** — category, province, importance
6. **Show "What Changed" badge** — highlights impact

### Demo 3: PakScholar — Scholarship Matcher (2 minutes)
1. **Navigate to /scholar**
2. **Type**: *"I'm a BS Computer Science student from Punjab with 3.5 CGPA, female"*
3. Show database matches with eligibility badges
4. **Show reasoning** for each match
5. **Show web matches** if no DB eligible (with "please verify" warning)

### Closing (30 seconds)
> "Three modules. One platform. Three languages. Zero cost. And the system gets smarter every day — PakGuide auto-enriches its database from successful web answers. This is PakMind — AI knowledge for Pakistan."

---

## Project Statistics

| Metric | Value |
|--------|-------|
| Total Backend Files | ~47 Python files |
| Total Frontend Files | ~35 TypeScript/TSX files |
| Lines of Code (Backend) | ~8,200+ |
| Lines of Code (Frontend) | ~4,500+ |
| Government Services Covered | 17+ |
| Languages Supported | 3 (English, Roman Urdu, Urdu Script) |
| API Endpoints | 14 |
| Database Tables | 8 |
| LLM Providers | 3 (with automatic failover) |
| Monthly API Cost | **$0** (all free-tier) |
| Processes Required | **2** (1 frontend + 1 backend) |

---

## Roadmap

- **PakGuide**: Expand to all 100+ government services, add office hours and appointment booking
- **PakWatch**: Push notifications for subscribed categories, SMS alerts for critical updates
- **PakScholar**: Partnership with HEC for direct database integration, application tracking
- **Mobile App**: React Native wrapper for the same backend
- **Community Contributions**: Allow verified users to submit corrections that improve the database
- **Analytics Dashboard**: Track most-asked questions to identify information gaps

---

*PakMind — Built for Pakistan. Powered by AI. Free for everyone.*
