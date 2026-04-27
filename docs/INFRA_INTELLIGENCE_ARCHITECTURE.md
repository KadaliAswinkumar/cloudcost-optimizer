# Infrastructure Intelligence — Target Architecture

This document defines how CloudCost connects to customer clouds, normalizes data, produces findings, reports, and alerts. It aligns with the **Infrastructure Intelligence Expansion Plan** (Phase 0–3).

## Goals

- **Least privilege**: read-only IAM / viewer roles by default; no destructive API calls in v1.
- **Multi-tenant isolation**: every row is scoped by `organization_id`; APIs enforce org boundaries.
- **Explainability**: each finding carries **evidence** (resource identifiers, rule version, query/snapshot reference).
- **Scalability**: long-running discovery runs as **async jobs**, not blocking HTTP requests.
- **Trust path**: **rule engine first**, AI for prioritization/narration second (optional).

## Logical Components

| Component | Responsibility |
|-----------|----------------|
| **Connectors** | Authenticate to AWS/GCP/Azure; pull inventory, IAM hints, networking, and (later) cost/usage APIs. |
| **Ingest** | Normalize provider payloads into a **versioned asset graph** JSON schema + optional denormalized tables later. |
| **Asset graph store** | Persist snapshots keyed by `scan_job_id`; diff snapshots for drift. |
| **Rule engine** | Deterministic checks (cost, security, architecture); outputs **findings** with severity and optional savings estimate. |
| **Report service** | Roll up findings into executive/engineering summaries (JSON + export formats later). |
| **Alerting** | Scheduled re-scan + threshold rules; deliver to webhook/email/Slack (channels configured per org). |
| **AI copilot** | Optional layer: explain findings, suggest remediation order (uses existing Groq path when configured). |

## Tenancy and Security Boundaries

- **Organization** (`organizations`): root tenant; all child entities reference `organization_id`.
- **Authentication (Phase 0+)**: Server-side JWT or session; map user → org membership (not implemented in this MVP slice; API uses explicit `org_id` path params for integration testing — replace with auth dependency before enterprise launch).
- **Connector secrets**: Stored **encrypted at rest** (Fernet derived from app secret; production should use a dedicated `INFRA_ENCRYPTION_KEY` or KMS — see `src/core/field_encryption.py`).
- **Audit**: Future `audit_events` table for connector create/rotate/scan (Phase 2).

## Data Flow

1. User registers a **cloud connector** (provider, display name, encrypted credentials blob).
2. User triggers **scan job** → status `pending` → worker/runner `running` → `completed` / `failed`.
3. **Collector** writes **asset snapshot** (JSONB graph: resources, edges, tags).
4. **Rule engine** reads snapshot → inserts/updates **findings** (idempotent by `rule_id` + `resource_id` + `scan_job_id` or latest scan).
5. **Report** aggregates findings for a time window.
6. **Alert rules** (future evaluation loop) compare new findings or cost deltas against thresholds.

## Asset Graph (v1 JSON Schema)

Version `1` top-level keys (extensible):

- `schema_version` (int)
- `captured_at` (ISO-8601)
- `provider` (`aws` | `gcp` | `azure`)
- `resources[]`: `{ "id", "type", "region", "name", "tags", "attributes" }`
- `edges[]`: `{ "from", "to", "rel" }` (e.g. `attached`, `in_subnet`, `member_of`)

Collectors may start with **stub/sample** graphs; real AWS/GCP/Azure SDK collectors plug into the same interface.

## API Surface (v1)

Base path: `/api/v1/intelligence`

- Organizations: CRUD minimal
- Connectors: create/list; credentials never returned in full
- Scan jobs: create (trigger scan), get status
- Findings: list with filters
- Reports: generate, get
- Alert rules: CRUD (evaluation loop stubbed)

See OpenAPI after `python scripts/export_openapi.py`.

## Observability

- Log `scan_job_id`, `organization_id`, `connector_id`, duration, outcome.
- Metrics (Phase 2): scans/hour, findings/rule, false-positive flags.

## Out of Scope (v1 code drop)

- Live breach detection / CVE feeds (requires licensed feeds and SOC workflows).
- Automatic remediation execution (Phase 3 playbook with approvals).
- Full CSPM parity (continuous control monitoring) — incremental rule packs instead.

## Related Documents

- [INFRA_INTELLIGENCE_PHASE1_RULES.md](./INFRA_INTELLIGENCE_PHASE1_RULES.md)
- [INFRA_INTELLIGENCE_90_DAY_WAVE.md](./INFRA_INTELLIGENCE_90_DAY_WAVE.md)
- [INFRA_INTELLIGENCE_GTM_BACKLOG.md](./INFRA_INTELLIGENCE_GTM_BACKLOG.md)
