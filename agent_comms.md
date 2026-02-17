# Agent Comms (Session Handoff)

- Goal handled: get app running in WSL with minimal setup, then implement Gemini-first model provider behavior in `apps/api`.
- Runtime constraints observed:
  - `docker` and `redis-server` unavailable in this environment.
  - Port binding from sandbox failed (`EPERM`), so servers were started unsandboxed.
- Minimal run path used:
  - API via `uvicorn` on `127.0.0.1:8000` with `INLINE_DEBATE_RUNNER=true`.
  - Web via Next.js dev server on `127.0.0.1:3000`.
- Provider logic implemented in API:
  - Added `GEMINI_API_KEY`, `GEMINI_MODEL`, `MODEL_PROVIDER` handling.
  - Resolution rule: Gemini default; OpenAI fallback when Gemini key missing; if both keys exist, `MODEL_PROVIDER` decides (`gemini`/`openai`), otherwise defaults to Gemini.
  - Updated LLM client setup to support Gemini through OpenAI-compatible endpoint.
  - Updated turn `model_metadata` to reflect live provider/model when configured.
- Validation run in `apps/api`:
  - `pytest -q` -> `13 passed`
  - `python -m compileall app` -> success
- After user added `GEMINI_API_KEY`, API was restarted and `/docs` returned `200`.
- Current commit scope request from user: include all latest local changes (including files modified during setup and existing local edits).
