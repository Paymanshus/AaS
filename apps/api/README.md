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
