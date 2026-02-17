"""Thin worker launcher for local scripts/tools."""

from pathlib import Path
import sys

API_ROOT = Path(__file__).resolve().parents[1] / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.workers import actors  # noqa: F401


if __name__ == "__main__":
    print("Use: PYTHONPATH=apps/api dramatiq app.workers.actors")
