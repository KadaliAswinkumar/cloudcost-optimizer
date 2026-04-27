# Enterprise and Global Market — Enhancement Backlog

Items that strengthen **investor narrative**, **enterprise readiness**, and **ecosystem adoption**. Not all are required for first revenue.

## Security and Compliance

- SSO (SAML 2.0 / OIDC) and SCIM provisioning.
- RBAC: org admin, viewer, connector admin, report-only.
- Immutable **audit log** (connector CRUD, scan runs, report exports, alert fires).
- Data residency options (region-specific deployment blueprint).
- SOC 2 Type II path: policies, access reviews, vendor subprocessors page.

## Product Depth

- **Commitment optimizer** (RI/Savings Plans/CUD) with confidence intervals from utilization.
- **Budgets and forecasts** with anomaly detection on cost + usage metrics.
- **Carbon / sustainability** signals where cloud carbon APIs exist.
- **What-if simulator** for topology changes (NAT removal, AZ expansion).

## Workflow and Collaboration

- Jira / Linear / ServiceNow ticket creation from a finding.
- Assignment + SLA tracking per finding; email digests.
- Exception workflow (accepted risk with expiry).

## Integrations (Partner Moat)

- Datadog / CloudWatch / GCP Monitoring for utilization-backed rules.
- PagerDuty / Opsgenie for alert routing.
- Slack / Microsoft Teams bots for scan summaries.
- Terraform / OpenTofu **plan-only** remediation PRs (approval-gated).

## MSP Mode

- Parent org with **child customer accounts**; delegated admin roles.
- White-label report PDF and custom domain for customer portal.

## Pricing and Packaging (illustrative)

- **Starter:** single cloud, weekly scan, email report.
- **Growth:** multi-account, daily scan, Slack + webhook alerts.
- **Enterprise:** SSO, audit, custom policy packs, VPC-hosted collector option.

## Investor Story Anchors

- **TAM/SAM:** cloud spend under management × attach rate for optimization + risk.
- **Defensibility:** normalized asset graph + rule packs + workflow integrations + proprietary utilization tuning.
- **Wedge:** start with fast FinOps savings, expand to continuous governance and remediation.

Cross-links: [ARCHITECTURE](./INFRA_INTELLIGENCE_ARCHITECTURE.md), [PHASE1_RULES](./INFRA_INTELLIGENCE_PHASE1_RULES.md), [90_DAY_WAVE](./INFRA_INTELLIGENCE_90_DAY_WAVE.md).
