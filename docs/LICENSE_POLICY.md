# CloudCost Optimizer License Policy

Last updated: May 2026

## 1. Licensing Position (Choose and Enforce One Model)

Two valid paths exist; select one and align repository/legal artifacts:

- **Open-source-first model:** keep the repository license (example: MIT) and monetize hosted service/support.
- **Commercial/proprietary model:** move core private, keep only selected components open, and use commercial SaaS terms.

Important: avoid mixed signals between `README`, `LICENSE`, contracts, and sales docs.

## 2. Open Source Usage

We may depend on open-source libraries. Their licenses are respected and disclosed through dependency manifests.

## 3. Internal Code Classification

- **Proprietary core:** recommendation engine logic, scoring methods, product workflows, reporting templates.
- **Configurable/customer-owned:** customer-specific connectors and operational policies.
- **Open-source dependencies:** third-party packages under their original licenses.

## 4. Redistribution

- Under open-source model: redistribution follows that license.
- Under commercial model: redistribution, resale, and sublicense are restricted unless contractually approved.

## 5. Contributor and Contractor Policy

- All contributors sign IP assignment or work-for-hire agreements.
- All external development work must include confidentiality and IP transfer clauses.

## 6. Commercial Packaging (Suggested)

- Starter: analytics + dashboards.
- Growth: recommendation workflow + anomaly operations.
- Enterprise: governance, approvals, custom integrations, SLA and support add-ons.
