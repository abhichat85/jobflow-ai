# JobFlow AI

An autonomous AI job-search agent that finds roles, tailors resumes, and applies on your behalf.

## Stack

- **Backend:** FastAPI · SQLAlchemy · Alembic · SQLite · Celery + Redis · Anthropic Claude API
- **Frontend:** Next.js 14 (App Router) · TanStack Query · Tailwind · shadcn/ui
- **Agents:** 10 specialized agents — profile ingest, profile synthesis, job parser, job scorer, resume tailor, cover letter, outreach writer, follow-up writer, interview prep, contact finder

## Prerequisites

- Python 3.12+
- Node 20+
- Redis (`brew install redis` on macOS, `apt install redis-server` on Linux)

## Quick start

```bash
# 1. Set your Anthropic API key
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY=sk-ant-...

# 2. Deploy everything (installs deps, migrates DB, starts all services)
make deploy

# 3. Open the app
open http://localhost:3000
```

**First-time setup:** Visit [http://localhost:3000/profile/ingest](http://localhost:3000/profile/ingest) to populate your profile from LinkedIn, resume, GitHub, and writing samples. The AI extracts everything and synthesizes your positioning, career narrative, and 5 resume variant angles. This drives all downstream job scoring and asset generation.

## Commands

| Command | What it does |
|---------|--------------|
| `make deploy` | Install deps, run migrations, start backend + worker + frontend |
| `make stop` | Stop all services |
| `make status` | Show which services are running |
| `make logs` | Tail all service logs |
| `make test` | Run backend tests |
| `make migrate` | Run database migrations only |
| `make clean` | Stop services and clear logs/pids |

## Service URLs

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API docs: http://localhost:8000/docs

## Project structure

```
backend/
  app/
    agents/        # 10 AI agents (profile_ingest, job_scorer, resume_tailor, ...)
    models/        # SQLAlchemy models (13 tables)
    routes/        # FastAPI routes (~40 endpoints)
    schemas/       # Pydantic schemas
    services/      # ClaudeService, ScraperService, PDF generator
  prompts/         # Agent system prompts (markdown)
  tests/           # pytest test suite
  alembic/         # Database migrations
frontend/
  app/             # Next.js App Router pages
  components/      # React components
  lib/api.ts       # Typed API client
scripts/
  deploy.sh        # One-command deployment
  stop.sh          # Stop all services
```
