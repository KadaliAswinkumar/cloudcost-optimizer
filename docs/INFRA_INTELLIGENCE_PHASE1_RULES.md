# Phase 1 Rule Pack — Priorities and Measurable Outputs

This document prioritizes **balanced** Phase 1 rules (cost + security + architecture) aligned with the expansion plan. Implemented v1 examples live in [`src/services/infra_intelligence/rule_engine.py`](../src/services/infra_intelligence/rule_engine.py) (stub graph in [`collector_stub.py`](../src/services/infra_intelligence/collector_stub.py)).

## Rule Output Contract

Each finding MUST include:

| Field | Purpose |
|-------|---------|
| `rule_id` | Stable identifier (`category.short_name.detail`). |
| `rule_version` | Semver for breaking changes / tuning. |
| `category` | `cost` \| `security` \| `architecture`. |
| `severity` | `critical` \| `high` \| `medium` \| `low` \| `info`. |
| `title` / `description` | Human-readable summary. |
| `evidence_json` | Resource IDs, matched config, connector reference, snapshot schema version. |
| `remediation_json` | Ordered steps or links to runbooks (optional). |
| `estimated_monthly_savings` | Decimal when cost-related; `null` otherwise. |
| `resource_key` | Dedupe key across rescans (`provider:resource:id[:suffix]`). |

## Cost and Waste (P0)

| Priority | `rule_id` (proposed) | Signal | Savings estimate |
|----------|----------------------|--------|------------------|
| P0 | `cost.stopped_instance.monthly_charge` | EC2 stopped + disks/EIP risk | Heuristic from attached volumes (stub uses fixed demo). |
| P0 | `cost.unattached_ebs_volume` | Volume `available` | Size × $/GB-month. |
| P0 | `cost.idle_load_balancer` | ALB/NLB with near-zero requests (needs metrics) | Monthly LB + LCU. |
| P1 | `cost.oversized_instance_family` | vCPU/memory vs utilization (needs CloudWatch/monitoring) | Rightsizing delta from catalog pricing. |
| P1 | `cost.nat_gateway_per_az_redundancy` | NAT count vs AZ coverage | Potential consolidation savings (careful with HA). |

## Security Posture (P0)

| Priority | `rule_id` (proposed) | Signal |
|----------|----------------------|--------|
| P0 | `security.sg.ssh_open_to_world` | `0.0.0.0/0` on port 22 (implemented on stub). |
| P0 | `security.sg_rdp_open_to_world` | `0.0.0.0/0` on 3389. |
| P0 | `security.public_s3_bucket_acl_or_policy` | Public read/list (AWS Config / S3 APIs). |
| P1 | `security.overprivileged_iam_policy` | `*:*` actions or admin-equivalent attachments. |
| P1 | `security.unencrypted_block_volume` | EBS not GP3 encrypted / CMK gaps. |

## Architecture and Complexity (P1)

| Priority | `rule_id` (proposed) | Signal |
|----------|----------------------|--------|
| P1 | `architecture.single_nat_gateway` | Single NAT in multi-AZ footprint (stub demo). |
| P1 | `architecture.cross_region_data_egress` | Peering/replication patterns with cost flags. |
| P2 | `architecture.spof_database` | Single-node DB without HA replica. |

## Explicit Non-Goals for Phase 1

- **CVE/breach intelligence** (requires licensed feeds, SOC workflows, and legal positioning).
- **Full CSPM control library** — start with high-signal network + IAM + storage rules.
- **Auto-remediation execution** — Phase 3 with approvals and audit.

## Expansion Order

1. Wire **real AWS collector** (read-only) populating the same `graph_json` schema.
2. Add **CloudWatch / Cost Explorer** joins for utilization and dollar-accurate savings.
3. Add **GCP** / **Azure** equivalents for top 10 resource types per provider.
4. Add **policy packs** (tagging standards, encryption mandates) as versioned JSON.

See also [INFRA_INTELLIGENCE_ARCHITECTURE.md](./INFRA_INTELLIGENCE_ARCHITECTURE.md).
