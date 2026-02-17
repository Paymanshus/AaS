# AGENTS.md

This file defines repository-specific guidance for AI coding agents working in this project.

## 1) Scope and Source of Truth

- Product intent: `PLAN.md`
- Requirement baseline: `PRD.md`
- Runtime setup: `README.md`, `START.md`
- API code: `apps/api`
- Worker entrypoint: `apps/worker`
- Web app: `apps/web`

If `PLAN.md` and code diverge, use `PRD.md` statuses (`DONE`/`PARTIAL`/`TODO`) to avoid accidental scope drift.

## 2) Working Rules

- Keep changes minimal and scoped to the user request.
- Prefer extending existing modules over creating parallel abstractions.
- Do not silently alter API contracts (`/v1` paths, event names, schema fields).
- Do not replace the local auth header model unless explicitly requested.
- Do not add new dependencies unless required for the task and clearly justified.
- Avoid destructive commands (`git reset --hard`, broad file deletion).

## 3) Project Map

- `apps/api/app/main.py`: FastAPI app + startup lifecycle.
- `apps/api/app/api/routes/arguments.py`: core create/join/ready/start/read/report/reaction APIs.
- `apps/api/app/api/routes/streaming.py`: websocket + SSE streaming endpoints.
- `apps/api/app/workers/runtime.py`: argument run loop + postprocess report generation.
- `apps/api/app/workers/actors.py`: Dramatiq queue actors.
- `apps/api/app/services/*`: reusable domain logic (events, credits, moderation, badges, reporting).
- `apps/api/app/db/models.py`: SQLAlchemy schema.
- `apps/web/app/app/page.tsx`: dashboard/create flow.
- `apps/web/app/arguments/[id]/page.tsx`: live/replay/report screen.

## 4) Local Run and Validation Commands

## Full stack (manual)

```bash
docker compose up -d redis
cd apps/api && python3 -m venv .venv && source .venv/bin/activate && pip install -e . && cp .env.example .env
cd apps/api && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000
cd apps/api && source .venv/bin/activate && PYTHONPATH=. dramatiq app.workers.actors
cd apps/web && npm install && npm run dev
```

## Required checks before handoff

```bash
cd apps/api && source .venv/bin/activate && pytest -q
cd apps/api && source .venv/bin/activate && python -m compileall app
cd /Users/paymanshu/_work/AaS && npm --workspace apps/web run lint
cd /Users/paymanshu/_work/AaS && npm --workspace apps/web run build
```

If dependencies are unavailable, report exactly what could not run.

## 5) API and Event Contract Notes

- Client auth in MVP uses headers:
  - `x-user-id`
  - `x-user-handle`
- REST audience query parameter: `audience_token`
- Web URL query parameter currently used by UI: `audienceToken`
- Websocket URL uses `userId` and optional `audienceToken`.

Core event types expected by UI:

- `turn.token`
- `turn.final`
- `turn.meta`
- `badge.awarded`
- `phase.changed`
- `argument.completed`
- `reaction.added`
- `error`

Preserve event payload compatibility when changing worker or streaming logic.

## 6) Data and State Invariants

- Start gate: minimum 2 ready participants.
- Persona gate: exactly 3 defend points required before ready.
- Credit rule: debit once per successful transition to `RUNNING`.
- Argument status flow: `waiting -> running -> completed|failed`.
- Replay ordering must follow persisted `turn_events` order.

Any change touching these invariants should include tests.

## 7) Testing Expectations for Changes

- Prefer `pytest` for backend unit/integration coverage.
- For API changes, add/update route-level tests.
- For worker logic changes, add runtime tests with deterministic `generate_turn_text` stubs.
- For frontend behavior changes in live/replay flows, add or update E2E coverage (Playwright preferred once added).

Use `PRD.md` test requirement section as the minimum coverage target.

## 8) Delivery Format for Agent Outputs

- Summarize what changed.
- List exact files touched.
- State which validations ran and their result.
- State what was not run (and why).
