# Vercel Python function: the Complecta (ALXNDRA) shopping-agent API as one FastAPI app.
# Every route of the demo host (/api/session, /api/chat SSE, /api/products, /api/cart …)
# is served by this function; sessions live in Neon (see examples/complecta/api/sessions_neon.py).
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# исходники семи пакетов репозитория — напрямую, без установки (см. requirements.txt)
for rel in ("commerce-common", "shopping-agent/core", "shopping-agent/runtime-messages-api",
            "merchant-agent/core", "merchant-agent/runtime-messages-api", "examples"):
    sys.path.insert(0, str(ROOT / rel))
os.environ.setdefault("DEMO_LOG_LEVEL", "INFO")

from complecta.api.main import app  # noqa: E402  (FastAPI instance Vercel serves)
