# AaS - Argument as a Service

Viral, chat-first AI argument arena.

## Monorepo layout

- `apps/web` - Next.js frontend (landing, dashboard, live argument chat/replay/wrapped)
- `apps/api` - FastAPI API + SQLAlchemy + streaming gateway
- `apps/worker` - Dramatiq worker entrypoint
- `infra/sql` - Supabase-flavored SQL helpers (RLS, bootstrap)

## Quick start

### 0) Redis

```bash
docker compose up -d redis
```

### 1) API + worker

```bash
cd apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

In another terminal:

```bash
cd apps/api
source .venv/bin/activate
PYTHONPATH=. dramatiq app.workers.actors
```

### 2) Web

```bash
cd apps/web
npm install
npm run dev
```

## Local auth model

Frontend uses a lightweight local login (handle + generated user id) and sends `x-user-id`/`x-user-handle` headers.
This keeps the MVP runnable before wiring Supabase Auth JWT verification.

If you want to run without worker/Redis in pure local mode, set `INLINE_DEBATE_RUNNER=true` in `apps/api/.env`.
If `OPENAI_API_KEY` is unset, agent turns fall back to deterministic template text for local/dev testing.

## Default URLs

- API: `http://localhost:8000`
- Web: `http://localhost:3000`
