# CloudCost Optimizer — Product Requirements Document (PRD)

**Version:** 1.1  
**Last updated:** April 2026  
**Status:** Production-oriented MVP with multi-cloud catalog, AI chat, and deploy paths (Render + GitHub Pages)

---

## 1. Vision

**CloudCost Optimizer** is a multi-cloud infrastructure cost intelligence product: users compare instance SKUs and pricing across **AWS, GCP, and Azure**, get **recommendations**, analyze **spot / preemptible** economics, and use **conversational AI** (Groq) to reason about workload fit and savings — from a single web app and API.

---

## 2. Goals

| Goal | Description |
|------|-------------|
| **Transparency** | Surface pricing and specs from APIs or curated demo data; avoid opaque “black box” numbers where possible. |
| **Multi-cloud** | Unified `cloud_instances` + `cloud_pricing` models for three providers. |
| **Actionable UI** | Dashboard, calculator, comparisons, spot intelligence, AI chat. |
| **Operable deploy** | Backend on **Render** (PostgreSQL); optional **GitHub Pages** for static UI; **no mandatory Redis** for core flows. |

---

## 3. Personas

- **Engineering lead / FinOps:** Compare instance types, regions, and pricing strategies; export mental model via UI + API.  
- **Founder / buyer:** High-level savings story, AI-assisted Q&A.  
- **Demo / investor:** Stable deploy, Swagger docs, predictable data seeding.

---

## 4. Functional requirements (implemented)

### 4.1 Data layer

- **PostgreSQL** with **Alembic** migrations.  
- Core tables: `cloud_instances`, `cloud_pricing` (multi-cloud); optional legacy AWS tables where still referenced.  
- **Initial migration** added so fresh DBs create tables before index migrations (fixes Render bootstrap).  
- **Seed script** `scripts/seed_demo_cloud_data.py` for demo SKUs; `--force` for re-seeding large catalogs.

### 4.2 Ingestion & scripts

- **`fetch_real_data.py`:** Pulls live-style catalog/pricing (GCP, Azure, AWS) with **`DATA_FETCH_PROFILE=lean`** default for small RAM/time budgets on free tier.  
- **`fetch_real_spot_pricing.py`:** Spot / preemptible pipeline with **batched inserts**, **per-provider caps**, and **OOM-safe** limits for Render **512Mi**.  
- **Cron / optional:** `scripts/fetch_real_spot_pricing.py` can run on a schedule where configured.

### 4.3 API (FastAPI)

- **OpenAPI 3** at `/openapi.json`; **Swagger UI** `/docs`; **ReDoc** `/redoc`; redirect `/swagger` → `/docs`.  
- **CORS** configurable via `CORS_ORIGINS` (required for GitHub Pages → Render API).  
- **Rate limiting:** Redis-backed when `REDIS_URL` set; otherwise permissive path for `/docs` and health.  
- **Redis:** Optional; app runs **without** Redis (no Upstash required).  
- **Groq:** `GROQ_API_KEY` / `GROQ_MODEL` via `pydantic-settings` + `python-dotenv` for **CloudCost AI™** chat.

### 4.4 Frontend (React + Vite)

- **Ports:** Dev UI **8080**, API **8801**, Vite proxy for `/api` and `/health`.  
- **GitHub Pages:** `base` + `BrowserRouter` basename `/cloudcost-optimizer/`; **`.nojekyll`**; workflow sets **`VITE_API_URL`** to production API.  
- **Spot Intelligence:** Instance dropdown aligned with **Cost Calculator** pattern (single `<select>`, labeled options).

### 4.5 Deployment

- **`render.yaml`:** Blueprint for API + static app + DB + cron; **`DATA_FETCH_PROFILE=lean`**; **no required Redis**.  
- **GitHub Actions** `.github/workflows/deploy.yml`: build and deploy static site to **GitHub Pages**.  
- **Documentation:** `README.md` (entry), `PRD.md` (this file), `INVESTOR_PITCH.md`, `docs/API.md`, `docs/openapi.json`.

### 4.6 Infrastructure Intelligence (in progress)

- **Purpose:** connect customer clouds (AWS/GCP/Azure), normalize an **asset graph**, run a **deterministic rule engine**, and surface **findings**, **reports**, and **alert rules** (evaluation loop to follow).  
- **API:** `/api/v1/intelligence/*` — see `docs/API.md` and architecture doc `docs/INFRA_INTELLIGENCE_ARCHITECTURE.md`.  
- **MVP collectors:** stub graph + sample rules in `src/services/infra_intelligence/`; real provider collectors replace stubs without changing the finding contract.  
- **Secrets:** connector payloads encrypted at rest via `src/core/field_encryption.py`; production should set **`INFRA_ENCRYPTION_KEY`**.  
- **Auth gap:** routes currently trust `org_id` in the path for integration tests — **server-side JWT + org membership** is required before enterprise positioning (see `README.md` security notes).  
- **Scan execution:** production uses `schedule_scan_job` (asyncio task) after the scan row is committed; pytest sets `INTELLIGENCE_SCAN_SYNCHRONOUS=1` to run `run_scan_job` on the request session (SQLite override).

---

## 5. Non-functional requirements

| Area | Target |
|------|--------|
| **Availability** | Health checks `/health`; readiness considers DB; cache optional. |
| **Security** | CORS, SQLAlchemy parameterization, env-based secrets; no secrets in repo. |
| **Observability** | Structured logging middleware; request IDs in logs. |
| **Testing** | `pytest` for API + cost calculator services; frontend ESLint + production build in CI scripts. |

---

## 6. Out of scope / known gaps

- **Backend JWT auth** is not implemented; the UI uses **demo auth** (localStorage). README must not claim server-side JWT until built.  
- **Celery** dependencies exist for optional workers; not required for the main API process.  
- **“Full” data profile** (`DATA_FETCH_PROFILE=full`) needs more RAM/time than free-tier web workers.

---

## 7. Historical changelog (high level)

- Multi-cloud schema + API routes.  
- Groq-powered chat + spot intelligence.  
- **Redis optional**; Render docs simplified (no Upstash).  
- **Alembic root migration** for `cloud_instances` / `cloud_pricing`.  
- **Lean fetch** for spot + regional data to prevent OOM on Render.  
- **GitHub Pages** workflow + `VITE_API_URL` + CORS guidance.  
- **Swagger** discoverability + rate-limit exceptions for docs.  
- Repo cleanup: single **PRD**, **pitch**, **API** index, **OpenAPI** artifact.

---

## 8. Success metrics (suggested)

- Deploy succeeds on Render + Pages without manual DB surgery.  
- `/health` + `/docs` load on production API.  
- UI loads catalog and runs analysis without CORS errors when origins are configured.  
- OpenAPI `docs/openapi.json` regenerated after route changes (`python scripts/export_openapi.py`).
