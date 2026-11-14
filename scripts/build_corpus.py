"""DEPRECATED (13 Nov 2026). Replaced by the layered pipeline:

    python -m pipelines.orchestration.run_all

This file only forwards to it so old instructions still work.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipelines.orchestration.run_all import main
sys.exit(main())
