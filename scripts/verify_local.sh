#!/usr/bin/env bash
# Local verification: pytest + frontend lint + build
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> pytest"
source venv/bin/activate
pytest tests/ -q

echo "==> frontend lint + build"
cd frontend
npm run lint
npm run build

echo "==> OK — ready for manual smoke tests (API + UI)"
