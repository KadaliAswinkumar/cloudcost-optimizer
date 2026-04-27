# Infrastructure Intelligence — 7-Day Delivery Sprint

This replaces a long phased calendar with a **single-week execution track** you can run with a small team. Goal: a **demo-grade vertical slice** (real or stubbed cloud read + findings in UI), not full enterprise parity—that follows in later sprints.

## What “done in a week” means

| In scope for 7 days | Out of scope (next sprints) |
|---------------------|-----------------------------|
| One cloud (pick **AWS** first) read-only inventory into `graph_json` | GCP/Azure collectors |
| Top ~10 high-signal rules wired to real data | Full 20+ rule pack |
| Findings list + scan trigger in the **web UI** | SSO, SOC2, MSP hierarchy |
| One report export (JSON or simple HTML/PDF) | Full exec branding suite |
| Async scan **job** (return 202 + poll, or background thread on worker) | Multi-region HA workers |

## Day-by-day (do in order)

**Day 1 — Lock the slice**  
- Confirm AWS account + IAM read-only policy template.  
- Add UI route shell: “Infrastructure Intelligence” → org (use single default org or create flow).

**Day 2 — AWS collector v0**  
- Replace stub for AWS connectors: EC2 describe, EBS describe, ELB describe, SG describe.  
- Map into existing `graph_json` schema ([architecture](./INFRA_INTELLIGENCE_ARCHITECTURE.md)).

**Day 3 — Rules on real graph**  
- Port 5–10 rules from [PHASE1_RULES](./INFRA_INTELLIGENCE_PHASE1_RULES.md) to run on live snapshot fields.  
- Tune `resource_key` + severity from real data.

**Day 4 — Async scan**  
- `POST .../scans` returns immediately with `pending`; worker completes job (Celery, Render background worker, or FastAPI `BackgroundTasks` for v0).  
- UI polls `GET .../scans/{id}` until `completed` / `failed`.

**Day 5 — Findings UX**  
- Table: severity, category, title, savings.  
- Detail drawer: evidence JSON + remediation steps.

**Day 6 — Report + alert stub**  
- “Generate report” from selected scan(s); download or view summary.  
- Store alert rules; optional: one webhook POST on new `high` finding (manual trigger first).

**Day 7 — Harden for demo**  
- Error states, empty states, copy for investors.  
- Run `alembic upgrade head` on staging; record a 3-minute Loom.

## Daily rhythm (together)

1. **Morning:** pick one ticket from the day row only.  
2. **Ship:** merge to `main` same day.  
3. **Evening:** 5-minute demo to each other; adjust Day N+1.

## After the week

Revisit [GTM backlog](./INFRA_INTELLIGENCE_GTM_BACKLOG.md) and split the next **one-week** slice (e.g. GCP narrow inventory, or SSO).
