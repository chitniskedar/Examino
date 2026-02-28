# Examino

> Adaptive MCQ practice system for PESU Semester 1 — with PDF-to-question generation.

![Python](https://img.shields.io/badge/Python-3.10+-yellow?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-yellow?style=flat-square)
![SQLite](https://img.shields.io/badge/SQLite-3-yellow?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

---

## What it does

- **Practice MCQs** from official PESU Question Banks across 6 subjects
- **Upload any PDF** — lecture notes, textbook chapters — and auto-generate MCQs from it
- **Tracks your accuracy** per topic and adjusts difficulty automatically
- **Syncs generated questions** back to the master `question_bank.json` so they're available permanently
- No database setup, no cloud — runs entirely on your machine

---

## Project Structure

```
smartstudy/
├── backend/
│   ├── main.py               # FastAPI app + all API endpoints
│   ├── models.py             # SQLAlchemy DB models (Question, Attempt, TopicStats)
│   ├── database.py           # DB helpers (CRUD, stats)
│   ├── question_engine.py    # Loads questions from question_bank.json on startup
│   ├── scheduler.py          # Adaptive difficulty logic
│   ├── pdf_service.py        # PDF text extraction + section splitting
│   ├── llm_question_gen.py   # MCQ generation (Claude API or heuristic fallback)
│   ├── qb_sync.py            # Syncs generated questions → question_bank.json
│   ├── migrate.py            # One-time DB migration script
│   ├── question_bank.json    # Master question bank (source of truth)
│   └── parser.py             # Text extraction utilities
├── frontend/
│   ├── index.html            # Single-file frontend (all pages)
│   ├── app.js                # Shared JS utilities
│   └── styles.css            # Global styles
├── data/                     # Auto-created — holds examino.db (git-ignored)
├── .gitignore
└── README.md
```
---

## How PDF Upload Works

```
PDF file
   │
   ▼
Extract text         pdfplumber → PyPDF2 → pypdf (fallback chain)
   │
   ▼
Split into sections  heading detection → 300-word chunks
   │
   ▼
Generate MCQs        Claude API (if key set) → heuristic fallback
   │
   ├──▶ Save to SQLite DB     (dedup by text hash)
   │
   └──▶ Sync to question_bank.json  (dedup by normalised text, atomic write, auto-backup)
```

---

## Adaptive Difficulty

After every attempt, `scheduler.py` adjusts the topic's difficulty:

| Accuracy | Result |
|---|---|
| > 75% | Promoted to harder difficulty |
| 40–75% | Stays at current difficulty |
| < 40% | Demoted to easier difficulty |

Minimum 3 attempts required before any adjustment.

---
## Tech Stack

- **Backend** — Python 3.10+, FastAPI, SQLAlchemy, SQLite
- **PDF parsing** — pdfplumber / PyPDF2 / pypdf
- **LLM** — Anthropic Claude API with heuristic fallback
- **Frontend** — HTML/CSS/JS, Space Grotesk + Space Mono, Anime.js
- **DB** — SQLite (zero config, file-based)
- **Render** — Hosting
