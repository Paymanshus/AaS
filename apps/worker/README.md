# AaS Worker

Worker lives as a separate process but shares the API package code.

Run with:

```bash
cd apps/api
source .venv/bin/activate
PYTHONPATH=. dramatiq app.workers.actors
```
