"""Vercel serverless entry point: the same FastAPI app (backend/app.py) serves /api/*, /ai/*, /docs.
The React app is served as static files by Vercel (see vercel.json)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app import app  # noqa: E402,F401
