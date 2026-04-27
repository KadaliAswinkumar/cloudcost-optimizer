# 90-Day Implementation Wave — Infrastructure Intelligence

High-level milestones for a small team (2–3 engineers). Adjust dates to your start week.

## Ownership (suggested)

| Area | Owner |
|------|--------|
| Platform / tenancy / auth | Backend lead |
| Connectors (AWS first) | Cloud engineer |
| Rule engine + reports | Backend + FinOps advisor |
| UI (onboarding, findings, reports) | Frontend lead |
| GTM / design partners | Founder |

## Weeks 1–2 — Platform shell

- Ship **organizations + connectors + scans + findings + reports + alert-rules** API (done in codebase v1).
- Add **server-side auth** dependency (JWT) and org membership model (replace path-only `org_id` trust).
- Harden **encryption** (`INFRA_ENCRYPTION_KEY` in production).
- Observability: structured logs for scan duration and outcome.

**Exit criteria:** authenticated user can onboard a connector and see findings in UI (stub or real).

## Weeks 3–5 — AWS read-only collector

- Implement `collector_aws` using least-privilege IAM role (external ID optional).
- Populate `graph_json` for: EC2, EBS, ELB, SG, VPC, NAT, IAM read-only summaries.
- Expand **rule_engine** with top 15 rules from [INFRA_INTELLIGENCE_PHASE1_RULES.md](./INFRA_INTELLIGENCE_PHASE1_RULES.md).

**Exit criteria:** one real AWS account produces non-stub findings; false-positive feedback loop started.

## Weeks 6–7 — Findings UX + reports

- Frontend: findings inbox (filter by severity/category), finding detail drawer with evidence JSON.
- PDF or HTML export of `InfraReport` (optional).
- Report templates: **Executive one-pager** vs **Engineering backlog**.

**Exit criteria:** pilot customer runs weekly report from UI.

## Weeks 8–9 — GCP + Azure (narrow)

- Second connector: **GCP** asset inventory (Compute, Firewall, GCS public access).
- Third: **Azure** (VM, NSG, Storage public access).
- Reuse same graph schema; provider-specific normalizers.

**Exit criteria:** multi-cloud demo on staging with 2+ providers.

## Weeks 10–12 — Monitoring + beta GTM

- Async job queue (Celery or managed worker) for long scans.
- **Alert evaluation** job: new critical findings or cost delta vs baseline.
- Beta pricing, 3–5 design partners, collect NPS + false-positive rate per rule.

**Exit criteria:** signed design partner LOI or paid pilot; rule FP rate documented.

## Beta Rollout Criteria

- P95 scan time under agreed SLO for pilot account size.
- Zero P0 security incidents from connector credentials handling.
- Runbook for credential rotation and org offboarding.
