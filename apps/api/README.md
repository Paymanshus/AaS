# AaS API

FastAPI backend for argument orchestration, streaming, and report generation.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

## Worker

```bash
source .venv/bin/activate
PYTHONPATH=. dramatiq app.workers.actors
```

## Model provider selection

- Default provider is Gemini when `GEMINI_API_KEY` is set.
- OpenAI is used as fallback when Gemini key is missing and `OPENAI_API_KEY` is set.
- When both keys are set, choose provider explicitly with `MODEL_PROVIDER` (`gemini` or `openai`).
