# CloudCost Optimizer - Complete Product + System Guide

Last updated: 2026-05-09

## 1) What this product is

CloudCost Optimizer is a full-stack SaaS-style platform for cloud cost reduction and operational decision support.

It combines:
- multi-cloud instance and pricing discovery,
- recommendation and simulation workflows,
- spot market risk analysis,
- infrastructure scan + rule-based findings,
- FinOps lifecycle tracking with investor-style KPI reporting,
- and conversational AI assistance.

In simple terms: it helps a team go from "we think cloud spend is high" to "here are prioritized actions, execution status, and verified savings."

---

## 2) What problem it solves

Most teams have one or more of these problems:
- cloud pricing is spread across providers and hard to compare,
- recommendations are generated but not tracked to completion,
- teams cannot prove realized savings over time,
- infra inefficiencies (security/cost/architecture) are detected late,
- leadership lacks clear metrics for action, confidence, and payback.

CloudCost Optimizer addresses all of those in one workflow.

---

## 3) Product modules (what users see)

The frontend exposes these primary product areas:

1. `Dashboard` (`/dashboard`)
2. `Cost Intelligence (FinOps)` (`/finops`)
3. `Savings Readiness` (`/readiness`)
4. `Infrastructure Intelligence` (`/infra-intelligence`)
5. `CloudCost AI` (`/ai`)
6. `Spot Intelligence` (`/spot-intelligence`)
7. `Get Recommendations` (`/recommendations`)
8. `Find Instances` (`/instances`)
9. `Compare Clouds` (`/compare`)
10. `Cost Calculator` (`/calculator`)

Public pages:
- `Landing`, `Login`, `Signup`,
- legal/support pages (`/privacy`, `/terms`, `/support`).

Note: current auth in this repo is demo-only localStorage auth (not server JWT).

---

## 4) High-level architecture (how it works end-to-end)

## Frontend
- React + Vite SPA (`frontend/src`)
- Axios API client (`frontend/src/api/client.js`)
- Tailwind-based UI
- Protected routes using local auth context

## Backend
- FastAPI app (`src/api/main.py`)
- Async SQLAlchemy with PostgreSQL
- Optional Redis (cache + rate limiting support)
- API routers for instances, pricing, recommendations, AI, spot, infra, FinOps

## Data and jobs
- PostgreSQL stores catalogs, pricing, findings, lifecycle events
- Infra scans run asynchronously in background tasks
- Spot history collection runs on a GitHub Actions schedule

## Deployment
- API on Render (with Postgres)
- UI on GitHub Pages or Render static site
- OpenAPI published and exportable

---

## 5) Repository map (what each major folder does)

- `src/api/` - FastAPI app, routers, middleware
- `src/models/` - SQLAlchemy models (catalog, pricing, infra, FinOps)
- `src/services/` - recommendation engines, collectors, AI, calculators
- `src/core/` - config, db session, cache, encryption
- `src/schemas/` - pydantic request/response schemas (infra module)
- `alembic/` - migrations
- `frontend/src/` - pages, components, auth context, api client
- `scripts/` - seeding, fetching, diagnostics, endpoint tests
- `tests/` - API and service tests
- `docs/` - product, architecture, IAM, legal, API docs

---

## 6) Backend application lifecycle and middleware

Implemented in `src/api/main.py`:
- startup:
  - initializes DB,
  - initializes Redis if configured,
  - app still starts even if optional subsystems fail.
- shutdown:
  - closes Redis and DB cleanly.

Middleware stack:
- request logging middleware (request IDs, timings, masked sensitive fields),
- gzip compression,
- rate limiter middleware (sliding window, Redis-backed if available),
- CORS with env-configured origins.

Global error handling:
- preserves HTTP and validation errors,
- catches unhandled exceptions,
- returns safe error payloads (less detail in production).

---

## 7) Data model (core tables and why they exist)

## 7.1 Cloud catalog and pricing

`cloud_instances`:
- unified instance inventory across AWS/GCP/Azure,
- vCPUs, memory, category, architecture, GPU flags.

`cloud_pricing`:
- on-demand/spot/preemptible/reserved style prices,
- region/zone and OS-aware entries.

`spot_price_history`:
- historical spot price points for trend and volatility analysis.

Legacy AWS-specific tables are also present:
- `ec2_instances`,
- `on_demand_pricing`,
- `reserved_pricing`,
- `spot_pricing`.

## 7.2 Recommendation lifecycle

`workload_profiles`, `recommendations`:
- input requirements + generated recommendation outputs.

## 7.3 Infrastructure Intelligence domain

Tables:
- `organizations`,
- `cloud_connectors`,
- `scan_jobs`,
- `asset_snapshots`,
- `infra_findings`,
- `infra_reports`,
- `alert_rules`.

Purpose:
- org-scoped cloud scan operations with evidence-backed findings and reports.

## 7.4 FinOps traction domain

Tables:
- `finops_recommendation_actions`,
- `finops_ingestion_sources`,
- `finops_action_events`,
- `finops_anomaly_events`.

Purpose:
- track insight -> acceptance -> implementation -> verification -> rollback.

---

## 8) API surface by product capability

Base prefix: `/api/v1` (except health and root).

## 8.1 Health
- `/health`
- `/health/ready`
- `/health/live`

## 8.2 Instances and catalog
- `/instances` (legacy AWS catalog)
- `/multicloud/instances` (main multi-cloud inventory endpoint)
- `/multicloud/stats`
- `/multicloud/providers`
- `/multicloud/categories`
- `/multicloud/instances/{provider}/{instance_type}`

## 8.3 Pricing and calculators
- `/pricing/on-demand/{instance_type}`
- `/pricing/spot/{instance_type}`
- `/pricing/spot/{instance_type}/history`
- `/pricing/spot/{instance_type}/risk`
- `/pricing/compare/{instance_type}`
- `/pricing/calculate`
- `/pricing/regions`
- `/multicloud/pricing/compare`

## 8.4 Recommendation engines
- `/recommendations`
- `/recommendations/quick`
- `/recommendations/right-size/{instance_type}`
- `/recommendations/workload-types`
- `/recommendations/interruption-tolerance`
- `/multicloud/recommendations`
- `/multicloud/compare/{instance_type}`

## 8.5 AI features
- `/ai/recommend`
- `/ai/chat`
- `/ai/suggestions`
- `/ai/workload-types`

## 8.6 Spot Intelligence
- `/spot-intelligence/analyze`
- `/spot-intelligence/compare`
- `/spot-intelligence/quick-check`
- `/spot-intelligence/history`

## 8.7 Infrastructure Intelligence
- org CRUD,
- connector create/list,
- async scan trigger + status,
- findings listing,
- cost summary + optimization brief,
- report generation + JSON export,
- alert rules create/list.

## 8.8 FinOps Intelligence
- dashboard payload,
- recommendation lifecycle actions,
- onboarding source status/health,
- growth leaderboard and weekly digest,
- anomaly list + acknowledge,
- what-if planner,
- copilot plan/execute,
- forecast,
- commitment optimizer,
- unit economics,
- policy validation,
- executive narrative,
- investor KPIs/report/export.

---

## 9) Feature-by-feature behavior (clear product explanation)

## 9.1 Dashboard
What it does:
- loads high-level cloud stats from `/multicloud/stats`,
- displays provider counts, region counts, and "max savings" context,
- includes quick cloud pricing comparison snapshot for a standard spec.

Why useful:
- fast sanity check that data and APIs are healthy,
- gives immediate top-level platform value.

## 9.2 Instance Finder
What it does:
- pulls up to 5,000+ instance rows via `/multicloud/instances`,
- supports search + provider + vCPU + memory + category + GPU filtering,
- paginates results on the client.

Why useful:
- one searchable catalog across AWS/GCP/Azure instead of provider consoles.

## 9.3 Compare Clouds
What it does:
- asks for required vCPU/RAM,
- calls `/multicloud/pricing/compare`,
- shows cheapest matching options per provider and cheapest overall.

Why useful:
- fast equivalent-cost decisioning when picking provider/SKU.

## 9.4 Cost Calculator
What it does:
- compute planning by count/hours/days using `/pricing/calculate`,
- compares scenarios for monthly and annual impact.

Why useful:
- turns raw hourly rates into budget-ready numbers.

## 9.5 Recommendations (multi-cloud)
What it does:
- takes workload constraints (CPU/RAM/provider/regions/budget/spot/GPU),
- calls `/multicloud/recommendations`,
- returns ranked recommendations with cost and fit context.

Why useful:
- converts raw catalog + price data into actionable shortlist decisions.

## 9.6 Spot Intelligence
What it does:
- per-instance analysis (`/spot-intelligence/analyze`):
  - on-demand vs spot savings,
  - volatility and interruption risk levels,
  - region guidance,
  - day-pattern risk visuals in UI.
- cross-provider spot comparison (`/spot-intelligence/compare`),
- quick summary endpoint (`/spot-intelligence/quick-check`),
- historical points endpoint (`/spot-intelligence/history`).

Why useful:
- unlocks 70-90% spot savings while exposing risk and mitigation context.

## 9.7 CloudCost AI Assistant
What it does:
- recommendation endpoint (`/ai/recommend`) for structured AI-style ranking,
- chat endpoint (`/ai/chat`) for natural language Q&A with DB context,
- prompt suggestions endpoint (`/ai/suggestions`),
- frontend supports voice input via browser speech APIs.

Why useful:
- lowers barrier to entry for non-expert users asking cloud cost questions.

## 9.8 Infrastructure Intelligence
What it does:
- create org workspace,
- add cloud connector with encrypted credentials at rest,
- run scan asynchronously (`202 Accepted`),
- poll scan status,
- fetch findings by scan/category,
- fetch optimization brief,
- fetch cost summary (if IAM has Cost Explorer permissions),
- generate exportable JSON report,
- define alert rules.

Live collection behavior:
- AWS with valid creds: real inventory + metrics + cost summary,
- no creds or non-AWS providers: deterministic stub graph for demo continuity.

Why useful:
- detects concrete security/cost/architecture issues with evidence and remediation.

## 9.9 FinOps Intelligence (Cost Intelligence Hub)
What it does:
- returns a comprehensive dashboard payload:
  - FOCUS-style views,
  - executive slices,
  - month-over-month trends,
  - top actions + confidence/risk.
- supports full recommendation lifecycle transitions:
  - accept, in-progress, implemented, verify, rollback, dismiss.
- tracks onboarding source quality and freshness.
- exposes growth loops:
  - leaderboard,
  - weekly digest,
  - what-if projection.
- anomaly tracking and acknowledgements.
- advanced controls:
  - copilot planning/execution,
  - 6-month savings forecast,
  - commitment optimizer,
  - unit economics,
  - policy validation.
- leadership outputs:
  - executive narrative markdown,
  - investor KPI payload,
  - investor JSON report export.

Why useful:
- this is the layer that proves outcomes, not just opportunities.

## 9.10 Savings Readiness
What it does:
- questionnaire scoring around ingestion, ownership, execution cadence, governance,
- computes readiness band (Developing/Strong/Elite etc),
- shows practical next actions.

Why useful:
- gives a maturity baseline and near-term improvement path.

---

## 10) Infrastructure Intelligence deep workflow (technical)

1) `POST /intelligence/organizations`
- creates tenant/workspace.

2) `POST /intelligence/organizations/{org_id}/connectors`
- stores provider + display name + encrypted credentials.

3) `POST /intelligence/organizations/{org_id}/connectors/{connector_id}/scans`
- creates `scan_job` with `pending`,
- either:
  - runs sync (test mode), or
  - commits and schedules background async task.

4) Background scan service:
- decrypts connector credentials,
- collects normalized asset graph:
  - EC2, EBS, security groups, NAT,
  - ELBv2, EKS + nodegroups,
  - RDS, ECS + services,
  - Lambda, S3, CloudWatch metrics,
  - Cost Explorer summary (if allowed),
- writes `asset_snapshot`,
- executes deterministic rule engine,
- persists `infra_findings`,
- dispatches webhook alerts (best effort),
- marks scan completed/failed.

5) Reporting:
- optimization brief endpoint summarizes top cost opportunities + guidance range,
- report endpoint aggregates findings and stores `summary_json`,
- export endpoint returns downloadable JSON artifact.

---

## 11) Rule engine logic (what it detects)

The rule engine (`infra_intelligence/rule_engine.py`) currently evaluates:

Security:
- security groups open to world (all traffic),
- open SSH/RDP to world.

Cost:
- stopped EC2 with residual costs,
- low CPU utilization rightsize candidates,
- old generation instance families,
- unattached EBS volumes,
- EKS nodegroup overprovisioning,
- missing Spot mix in EKS nodegroups,
- RDS gp2 -> gp3 opportunities,
- ECS overprovision/low utilization patterns,
- Lambda high-memory or low-traffic inefficiencies,
- S3 buckets without lifecycle policies,
- low commitment coverage (RI/SP),
- high spend concentration by service from cost summary.

Architecture:
- single NAT bottleneck,
- single-AZ RDS resilience concern.

Each finding includes:
- rule id/version,
- severity/category,
- evidence JSON,
- remediation steps,
- optional estimated monthly savings.

---

## 12) FinOps traction workflow (technical)

Core idea: recommendations are only valuable when moved through a measurable lifecycle.

Lifecycle states:
- `open` -> `accepted` -> `in_progress` -> `implemented` -> `verified`
- with optional `dismissed` and `rolled_back`.

What the backend computes:
- activation:
  - time-to-first-saving,
  - source onboarding completion.
- impact:
  - identified vs implemented vs realized savings.
- adoption:
  - active orgs,
  - acceptance and repeat action rates.

Anomaly auto-detection:
- savings regression (weekly drop),
- opportunity backlog pressure (large unrealized gap).

Investor outputs:
- gross/net savings,
- implementation and verification counts,
- confidence and rollback metrics,
- payback period estimate,
- exportable report JSON.

---

## 13) Recommendation and scoring engines (how ranking works)

`RecommendationEngine` (AWS legacy) and `MultiCloudRecommender` (cross-cloud) implement:
- filtering by required resources and constraints,
- candidate pricing retrieval,
- cost/fit/performance/risk scoring,
- tolerance-aware interruption filtering,
- ranking and explanation formatting.

Output generally includes:
- candidate specs,
- hourly/monthly cost,
- savings percentages,
- strategy/risk context,
- ranked recommendation order.

---

## 14) Spot intelligence internals

`SpotIntelligence` service:
- fetches on-demand + spot price views,
- computes averages/min/max and volatility,
- calculates risk level and recommendation text,
- compares options across providers,
- can use historical price records when available.

`SpotPriceTracker` and history table support:
- trend statistics,
- interruption risk estimation,
- best zone suggestions.

Scheduled data collection:
- GitHub Actions weekly workflow triggers script to collect fresh spot data.

---

## 15) AI internals and behavior

Two AI tracks:

1) Structured AI recommendation (`CloudCostAI`)
- workload-type-aware scoring,
- provider-aware filtering and pricing pulls,
- recommendation insights synthesis.

2) Conversational AI (`ConversationalAI`)
- takes user message + conversation history,
- optionally enriches from DB context,
- calls Groq API when `GROQ_API_KEY` configured,
- returns assistant response + usage fields.

If AI key is missing/unavailable:
- chat/recommendation surfaces error state instead of hard crashing.

---

## 16) Reliability and resilience design

Observed resilience patterns in code:
- endpoint-level try/except with graceful fallback payloads,
- per-provider isolation in comparison endpoints,
- partial stats return when one query fails,
- safe type conversions and null handling,
- global exception handling + structured logs,
- optional Redis behavior (degrades gracefully when absent),
- background scan failure capture + status updates.

Result:
- product favors partial useful responses over full endpoint failure.

---

## 17) Security model (current state)

Implemented:
- encrypted connector secrets at rest (`field_encryption.py`),
- CORS enforcement,
- parameterized ORM usage,
- sensitive request log masking,
- optional rate limiting,
- org-scoped infra entities.

Important current caveat:
- frontend auth is demo/localStorage, not server-verified auth.
- before enterprise production, add backend authN/authZ and role enforcement.

---

## 18) Local setup and run flow

`setup-local.sh` automates:
- Python version check,
- virtualenv + dependencies,
- Podman Postgres + Redis containers,
- migrations (`alembic upgrade head`),
- optional demo seed,
- import and connectivity checks.

Then:
- `./start-backend.sh` -> API,
- `./start-frontend.sh` -> UI.

---

## 19) Deployment and CI/CD flow

Render (`render.yaml`):
- Python web service for API,
- static site service for frontend (optional path),
- managed Postgres,
- optional cron job for spot collection.

GitHub Pages workflow:
- builds frontend on `main`,
- sets `VITE_API_URL`,
- deploys static bundle.

GitHub Actions spot workflow:
- scheduled weekly price collection script run.

---

## 20) Testing and validation in repo

Automated tests cover:
- core API health and key endpoints,
- recommendations/pricing/instances behavior,
- infrastructure intelligence async scan + findings/report export flow,
- FinOps lifecycle + growth + anomalies + investor endpoints,
- cost calculator service logic.

Scripts provide practical deployment checks:
- endpoint smoke tests,
- comprehensive remote test script.

---

## 21) Known current limitations

1. Auth:
- UI auth is demo-only; no backend JWT/session enforcement yet.

2. Infra collectors:
- deep live support currently strongest for AWS.
- GCP/Azure infra intelligence path currently uses stub graph until full collectors ship.

3. Some dashboard datasets:
- FinOps dashboard includes deterministic demo data merged with real lifecycle metrics.

4. Enterprise controls:
- advanced RBAC/SSO/audit governance are roadmap-level, not fully implemented here.

---

## 22) End-to-end "how all works" in one sequence

1) User signs in (demo auth), enters app.
2) Uses catalog/comparison/recommendation tools to identify opportunities.
3) Runs infra scan to discover concrete findings with evidence.
4) FinOps module tracks selected actions through lifecycle states.
5) System computes impact/adoption/activation metrics and anomaly signals.
6) Spot intelligence + AI assist with risk-aware optimization decisions.
7) Leadership exports investor and executive summaries proving progress.

This is the core value chain:
**Discovery -> Prioritization -> Execution -> Verification -> Reporting**.

---

## 23) Quick interview summary you can say

"CloudCost Optimizer is a full-stack FinOps + Infra intelligence platform. It aggregates multi-cloud instance and pricing data, generates recommendation and spot-risk insights, runs asynchronous infrastructure scans with rule-based findings, and tracks recommendation lifecycle to verified savings with investor-grade KPI reporting. The backend is FastAPI + async SQLAlchemy + PostgreSQL, the frontend is React/Vite, and the system is deployable on Render + GitHub Pages with scheduled spot data collection."

