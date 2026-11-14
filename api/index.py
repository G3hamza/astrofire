"""Vercel entry point: the same FastAPI app (backend/app.py) serves everything: the built React app, /lite, /api/*, /ai/*, /docs.
Vercel installs requirements.txt and builds frontend-app (see vercel.json)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app import app  # noqa: E402,F401
