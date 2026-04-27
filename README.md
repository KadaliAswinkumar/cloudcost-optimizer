# CloudCost Optimizer

**Multi-cloud instance catalog, pricing, spot intelligence, and AI-assisted cost Q&A** — FastAPI backend + React (Vite) UI.

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18-blue.svg)](https://reactjs.org/)
[![License MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

| Document | Purpose |
|----------|---------|
| **[PRD.md](PRD.md)** | Product scope, requirements, and changelog |
| **[INVESTOR_PITCH.md](INVESTOR_PITCH.md)** | Slide-style narrative for fundraising |
| **[docs/API.md](docs/API.md)** | How to read the API spec |
| **[docs/openapi.json](docs/openapi.json)** | OpenAPI 3 schema (`python scripts/export_openapi.py` to refresh) |

---

## Features

- **Multi-cloud catalog** — AWS, GCP, Azure instance types in unified tables (`cloud_instances`, `cloud_pricing`).
- **Dashboard & tools** — Cost calculator, comparisons, recommendations, spot intelligence.
- **CloudCost AI™** — Groq chat (`GROQ_API_KEY`); optional if unset.
- **Infrastructure Intelligence** — orgs, cloud connectors, scans, findings, reports, alert rules (`/api/v1/intelligence/*`); see `docs/INFRA_INTELLIGENCE_ARCHITECTURE.md`.
- **API-first** — Swagger UI at `/docs`, `/openapi.json` on the API host.
- **Deploy-friendly** — Backend on **Render** (PostgreSQL); UI on **GitHub Pages** or any static host; **Redis optional**.

---

## Quick start (local)

```bash
./setup-local.sh          # Podman + Postgres + Redis + venv + migrations
./start-backend.sh        # API → http://localhost:8801
./start-frontend.sh       # UI  → http://127.0.0.1:8080 (proxies /api to API)
```

- **API docs:** http://localhost:8801/docs  
- **Demo data:** `python scripts/seed_demo_cloud_data.py` if the catalog is empty.

**Groq:** set `GROQ_API_KEY` in `.env` (see `.env.example`).

---

## Repository layout

```
cloudcost-optimizer/
├── src/                 # FastAPI app, services, models
├── frontend/            # React + Vite
├── alembic/             # DB migrations
├── scripts/             # Data fetch, seed, export_openapi.py
├── docs/
│   ├── API.md           # API spec index
│   └── openapi.json     # Generated OpenAPI (committed for review/CI)
├── tests/               # pytest
├── render.yaml          # Render Blueprint
└── .github/workflows/   # GitHub Pages deploy for frontend
```

---

## API specification

- **Interactive:** `https://<your-api-host>/docs` (also `/swagger` → `/docs`)  
- **Machine-readable:** [docs/openapi.json](docs/openapi.json)  
- **Details:** [docs/API.md](docs/API.md)

Regenerate after route changes:

```bash
python scripts/export_openapi.py
```

---

## Configuration

Copy `.env.example` → `.env`. Important keys:

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | Async Postgres URL (`postgresql+asyncpg://...`) |
| `CORS_ORIGINS` | Comma-separated origins (no spaces) — **required** for GitHub Pages → API |
| `GROQ_API_KEY` | CloudCost AI chat |
| `DATA_FETCH_PROFILE` | `lean` (default) vs `full` for data scripts |

**Redis:** omit `REDIS_URL` on Render if you do not use Redis; the API runs without cache.

---

## Testing & quality

```bash
./test-local.sh           # pytest + frontend lint + production build
# or
pytest
cd frontend && npm run lint && npm run build
```

---

## Deployment (summary)

| Layer | Option |
|-------|--------|
| **API + DB** | [Render](https://render.com) with `render.yaml` or manual Web Service + Postgres |
| **Static UI** | GitHub Actions → GitHub Pages (`.github/workflows/deploy.yml`) |
| **Env** | Set `VITE_API_URL` in the Pages workflow (or repo variable) to your real API URL |

Production checklist: `CORS_ORIGINS` includes your Pages origin (`https://<user>.github.io`), `SECRET_KEY` set, `DEBUG=false`, `ENVIRONMENT=production`.

**GitHub Pages → Render API:** The dashboard calls the API from the browser. If stats stay on `...` or show an error banner, open DevTools → Network: the `/api/v1/multicloud/stats` request is usually **blocked by CORS**. On the Render web service, set `CORS_ORIGINS` to a comma-separated list (no spaces) that includes **`https://<github-username>.github.io` exactly** — not `https://<user>.github.io/<repo>`, because the browser’s `Origin` header never includes the repo path. Redeploy the API after changing env vars.

Sanity check from a terminal (should list `access-control-allow-origin` when the origin is allowed):

```bash
curl -sI -H "Origin: https://YOURUSER.github.io" "https://YOUR-API.onrender.com/api/v1/multicloud/stats" | grep -i access-control
```

---

## Security notes

- **UI auth** is a **demo** (localStorage). There is **no server-side JWT** in this repo yet — do not market enterprise auth until implemented.
- CORS, parameterized SQL, and env-based secrets are used; rotate any leaked keys immediately.

---

## Contributing

1. Branch from `main` (e.g. `feature/...`).  
2. Run `./test-local.sh` or equivalent.  
3. Keep PRs focused; update `docs/openapi.json` if you change routes.

---

## License

MIT — see [LICENSE](LICENSE).

---

**Questions?** Open an issue or extend the **PRD** for internal planning.
