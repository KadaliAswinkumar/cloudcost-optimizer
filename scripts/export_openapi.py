#!/usr/bin/env python3
"""
Export OpenAPI 3 schema to docs/openapi.json (see docs/API.md).

  python scripts/export_openapi.py

Requires the same env as the app (minimal: no DB connection at export time if
models only register routes; DB may load via settings — use dummy DATABASE_URL).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Allow export without a real Postgres (pydantic loads .env if present)
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/cloudcost")
# Production-shaped export: omit debug-only routes from the published schema
os.environ["DEBUG"] = "false"
os.environ["ENVIRONMENT"] = "production"

from src.api.main import app  # noqa: E402


def main() -> None:
    out = project_root / "docs" / "openapi.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    schema = app.openapi()
    out.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    print(f"Wrote {out} ({len(schema.get('paths', {}))} paths)")


if __name__ == "__main__":
    main()
