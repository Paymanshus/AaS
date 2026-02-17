# AaS MVP Startup Checklist

1. Start Redis (`docker compose up -d redis`).
2. Start API (`cd apps/api && python3 -m venv .venv && source .venv/bin/activate && pip install -e . && uvicorn app.main:app --reload --port 8000`).
3. Start worker (`cd apps/api && source .venv/bin/activate && PYTHONPATH=. dramatiq app.workers.actors`).
4. Start web (`cd apps/web && npm install && npm run dev`).
5. Open `http://localhost:3000`, login with handle, create argument, invite participants.
