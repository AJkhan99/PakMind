<div align="center">

# 🇵🇰 PakMind

### Pakistan's AI Knowledge Platform

**Government services · Policy updates · Scholarship matching — in English, Roman Urdu & اردو**

[![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=next.js)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react)](https://react.dev)
[![Supabase](https://img.shields.io/badge/Supabase-pgvector-3ECF8E?logo=supabase)](https://supabase.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

</div>

---

## 📖 What is PakMind?

220 million Pakistanis face a daily information gap — government procedures are scattered across dozens of English-only websites, policy changes are buried in gazettes, and scholarship worth billions of rupees go unclaimed every year.

**PakMind closes that gap** with three AI-powered modules on a single platform:

| Module | Route | What it answers |
|--------|-------|-----------------|
| 🧭 **PakGuide** | `/guide` | *"How do I get a passport?"* — 17+ government services with requirements, steps, fees, PDF checklists, office locators |
| 👁 **PakWatch** | `/watch` | *"What changed in the budget?"* — policy updates, petrol prices, notifications with hot-topic digests |
| 🎓 **PakScholar** | `/scholar` | *"Which scholarships am I eligible for?"* — AI eligibility matching against verified + live-web opportunities |

Ask in **English**, **Roman Urdu** (*"passport kaise banwayen?"*), or **Urdu script** (*"پاسپورٹ کیسے بنوائیں؟"*) — smart routing automatically sends your question to the right module.

---

## ✨ Key Features

- 🗣 **Trilingual by design** — English, Roman Urdu & Urdu script (native, not translated)
- 🎤 **Voice input** — speak your question in English or Urdu
- ✅ **Dual-LLM verification** — every answer is cross-checked by a second independent LLM to reduce hallucinations
- 🌐 **Deep government scraping** — when the DB is weak, PakGuide scrapes live `.gov.pk` pages for ground-truth content
- 🧠 **Self-learning database** — successful web answers are auto-cached back into the DB, so the system gets smarter with every query
- 📄 **PDF checklist generator** — download printable application checklists with fee calculators
- 💰 **$0 API cost** — runs entirely on free tiers (Gemini, Groq, Supabase, Serper)
- 🔀 **LLM failover chain** — Google Gemini → Groq → OpenAI with automatic key rotation on quota limits

---

## 🏗 Architecture

```
┌──────────────────────────────┐         ┌──────────────────────────────┐
│   PakMind Frontend (:3000)   │   HTTP  │    PakMind Backend (:8000)   │
│   Next.js 16 · React 19      │ ──────► │    FastAPI · Python          │
│                              │         │                              │
│  /        Smart search +     │         │  /api/guide    5-phase RAG   │
│  /guide   PakGuide UI        │         │  /api/watch    3-way RAG +   │
│  /watch   PakWatch UI        │         │                 grounded web │
│  /scholar PakScholar UI      │         │  /api/scholar  2-phase match │
│                              │         │  /api/feedback ratings + PDF │
└──────────────────────────────┘         └──────────────┬───────────────┘
                                                        │
                         ┌──────────────────────────────┼──────────────┐
                         ▼                              ▼              ▼
                 ┌──────────────┐              ┌──────────────┐ ┌───────────┐
                 │ Google Gemini│ ──429────►  │  Groq Llama  │ │  OpenAI   │
                 │  (primary)   │  key rotate │ (verification)│ │ (optional)│
                 └──────────────┘              └──────────────┘ └───────────┘
                         │
                         ▼
                 ┌──────────────────────────────────────────────┐
                 │ Supabase (PostgreSQL + pgvector)              │
                 │ sources · documents · document_chunks         │
                 │ government_services · government_updates      │
                 │ opportunities · topic_digests · web_answers   │
                 └──────────────────────────────────────────────┘
```

**Two processes run the entire platform** — one frontend, one backend.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Supabase project (free) + free API keys (see table below)

### 1. Get free API keys

| Service | Where | Used for |
|---------|-------|----------|
| [Google Gemini](https://aistudio.google.com/apikey) | AI Studio | Primary LLM + embeddings |
| [Groq](https://console.groq.com/keys) | Console | Verification LLM |
| [Supabase](https://supabase.com) | Dashboard → Settings → API | Database (URL + anon key + service-role key) |
| [Serper.dev](https://serper.dev) | Dashboard | Google web search |

### 2. Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# → Edit .env with your API keys

# Run
uvicorn app.main:app --reload --port 8000
```

The API is now live at `http://localhost:8000` — interactive docs at `/docs`.

### 3. Frontend

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# → Set NEXT_PUBLIC_API_URL=http://localhost:8000

# Run
npm run dev
```

Open `http://localhost:3000` — done! 🎉

---

## 📡 API Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/guide/query` | POST | Full RAG answer for government services |
| `/api/guide/search` | POST | Service search (no AI generation) |
| `/api/watch/query` | POST | Policy update answers with verification |
| `/api/watch/latest` | GET | Latest updates (filter by category/province) |
| `/api/watch/topics` | GET | Pre-computed hot-topic digests |
| `/api/scholar/query` | POST | Two-phase scholarship eligibility matching |
| `/api/scholar/opportunities` | GET | Browse all opportunities |
| `/api/feedback/submit` | POST | Rate an answer |
| `/api/feedback/checklist` | POST | Generate PDF checklist |
| `/health` | GET | System health check |

Full interactive documentation: `http://localhost:8000/docs`

---

## 🛠 Tech Stack

**Frontend** — Next.js 16 (App Router, Turbopack) · React 19 · TypeScript 5 · Tailwind CSS 4 · Framer Motion · Noto Nastaliq Urdu

**Backend** — FastAPI · Pydantic v2 · Supabase (PostgreSQL + pgvector) · httpx · BeautifulSoup4 · fpdf2

**AI** — Google Gemini (REST, free tier) · Groq Llama (verification) · gemini-embedding-001 (1536-dim) · Gemini grounded search · Serper.dev + DuckDuckGo (web search)

---

## 🔒 Security

- IP-based rate limiting (20 req/min default)
- CORS allow-list, request size limit (1MB), security headers
- Secrets exclusively in `.env` (gitignored) — never in source
- AI answers carry confidence tiers + source-attribution warnings

---

## 📂 Repository Structure

```
PakMind/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app — routers, middleware, scheduler
│   │   ├── config.py          # Unified pydantic-settings
│   │   ├── ai/                # Shared LLM router + embeddings (key rotation)
│   │   ├── db/                # Supabase client + all table helpers
│   │   ├── guide/             # PakGuide domain (retrieval, scraping, PDF)
│   │   ├── watch/             # PakWatch domain (RAG, digests, web cache)
│   │   ├── scholar/           # PakScholar domain (eligibility matching)
│   │   └── shared/            # Feedback API
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── app/               # /, /guide, /watch, /scholar routes
│   │   ├── components/        # Landing + per-module component folders
│   │   ├── lib/               # API client + smart search router
│   │   └── types/
│   ├── package.json
│   └── .env.example
├── PRESENTATION.md            # Full product presentation
└── README.md
```

---

## 📜 License

MIT — free to use, modify, and build upon.

---

<div align="center">

**PakMind** — Built for Pakistan · Powered by AI · Free for everyone

</div>
