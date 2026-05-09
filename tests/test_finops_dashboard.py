"""FinOps dashboard API smoke tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_finops_dashboard_returns_demo_payload(client: AsyncClient) -> None:
    r = await client.get("/api/v1/finops/dashboard")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["meta"]["data_mode"] == "demo"
    assert "focus" in data and "executive" in data
    assert "impact" in data and "adoption" in data and "activation" in data
    assert data["focus"]["region_word_cloud"][0]["name"]
    assert data["mom_trends"]["series"]
    assert data["top_actions"]
    assert data["top_actions"][0]["confidence_level"] in {"high", "medium", "low"}
    assert "risk_score" in data["top_actions"][0]


@pytest.mark.asyncio
async def test_finops_action_and_growth_flow(client: AsyncClient) -> None:
    org = "pytest-org"

    dash = await client.get("/api/v1/finops/dashboard", params={"organization_slug": org})
    assert dash.status_code == 200, dash.text
    top = dash.json()["top_actions"]
    assert top
    recommendation_id = top[0]["recommendation_id"]

    accept = await client.post(
        f"/api/v1/finops/recommendations/{recommendation_id}/accept",
        json={"organization_slug": org, "actor": "tester"},
    )
    assert accept.status_code == 200, accept.text
    assert accept.json()["status"] == "accepted"

    implemented = await client.post(
        f"/api/v1/finops/recommendations/{recommendation_id}/implemented",
        json={"organization_slug": org, "actor": "tester", "realized_monthly_savings_usd": 1234},
    )
    assert implemented.status_code == 200, implemented.text
    assert implemented.json()["status"] == "implemented"

    in_progress = await client.post(
        f"/api/v1/finops/recommendations/{recommendation_id}/in-progress",
        json={"organization_slug": org, "actor": "tester"},
    )
    assert in_progress.status_code == 200, in_progress.text
    assert in_progress.json()["status"] == "in_progress"

    verified = await client.post(
        f"/api/v1/finops/recommendations/{recommendation_id}/verify",
        json={
            "organization_slug": org,
            "actor": "tester",
            "verification_notes": "kpi delta verified",
            "realized_monthly_savings_usd": 1111,
        },
    )
    assert verified.status_code == 200, verified.text
    assert verified.json()["status"] == "verified"

    onboard = await client.post(
        "/api/v1/finops/onboarding/sources",
        json={
            "organization_slug": org,
            "source_type": "aws_cur",
            "status": "connected",
            "freshness_status": "fresh",
            "records_ingested": 9000,
            "confidence_score": 0.9,
            "details_json": {"bucket": "demo-cur"},
        },
    )
    assert onboard.status_code == 200, onboard.text

    digest = await client.get("/api/v1/finops/growth/weekly-digest", params={"organization_slug": org})
    assert digest.status_code == 200, digest.text
    assert digest.json()["impact_summary"]["realized_savings_30d_usd"] >= 1111

    leaderboard = await client.get("/api/v1/finops/growth/leaderboard")
    assert leaderboard.status_code == 200, leaderboard.text
    assert any(row["organization_slug"] == org for row in leaderboard.json()["leaderboard"])

    what_if = await client.post(
        "/api/v1/finops/growth/what-if",
        json={
            "organization_slug": org,
            "recommendation_ids": [recommendation_id],
            "adoption_probability": 0.7,
        },
    )
    assert what_if.status_code == 200, what_if.text
    assert what_if.json()["projected_monthly_savings_usd"] > 0

    anomalies = await client.get("/api/v1/finops/anomalies", params={"organization_slug": org})
    assert anomalies.status_code == 200, anomalies.text
    rows = anomalies.json()["anomalies"]
    assert rows
    assert any(r.get("details", {}).get("auto_detected") for r in rows)

    ack = await client.post(
        f"/api/v1/finops/anomalies/{rows[0]['id']}/acknowledge",
        json={"organization_slug": org, "actor": "tester"},
    )
    assert ack.status_code == 200, ack.text
    assert ack.json()["status"] == "acknowledged"

    rollback = await client.post(
        f"/api/v1/finops/recommendations/{recommendation_id}/rollback",
        json={"organization_slug": org, "actor": "tester", "rollback_reason": "test rollback"},
    )
    assert rollback.status_code == 200, rollback.text
    assert rollback.json()["status"] == "accepted"

    investor = await client.get("/api/v1/finops/investor/kpis", params={"organization_slug": org})
    assert investor.status_code == 200, investor.text
    kpis = investor.json()["kpis"]
    assert "average_confidence_score" in kpis
    assert kpis["recommendations_implemented"] >= 0
    assert "recommendations_verified" in kpis
    assert kpis["recommendations_rolled_back"] >= 1

    report = await client.get("/api/v1/finops/investor/report", params={"organization_slug": org})
    assert report.status_code == 200, report.text
    assert report.json()["meta"]["format"] == "investor_report_v1"

    report_export = await client.get("/api/v1/finops/investor/report/export", params={"organization_slug": org})
    assert report_export.status_code == 200, report_export.text
    assert "attachment;" in report_export.headers.get("content-disposition", "")

    copilot_plan = await client.post(
        "/api/v1/finops/copilot/plan",
        json={
            "organization_slug": org,
            "recommendation_ids": [recommendation_id],
            "risk_threshold": 0.7,
            "approval_mode": "auto_if_low_risk",
            "change_window": "business_hours",
        },
    )
    assert copilot_plan.status_code == 200, copilot_plan.text
    assert copilot_plan.json()["summary"]["recommendation_count"] >= 1

    copilot_execute = await client.post(
        "/api/v1/finops/copilot/execute",
        json={
            "organization_slug": org,
            "recommendation_ids": [recommendation_id],
            "approved": True,
            "dry_run": False,
        },
    )
    assert copilot_execute.status_code == 200, copilot_execute.text
    assert copilot_execute.json()["ok"] is True

    forecast = await client.get("/api/v1/finops/forecast", params={"organization_slug": org, "months": 6})
    assert forecast.status_code == 200, forecast.text
    assert len(forecast.json()["projection"]) == 6

    commitment = await client.get("/api/v1/finops/commitment/optimizer", params={"organization_slug": org})
    assert commitment.status_code == 200, commitment.text
    assert "recommendations" in commitment.json()

    unit_econ = await client.post(
        "/api/v1/finops/unit-economics",
        json={
            "organization_slug": org,
            "monthly_revenue_usd": 200000,
            "monthly_active_customers": 1000,
            "monthly_transactions": 250000,
        },
    )
    assert unit_econ.status_code == 200, unit_econ.text
    assert "unit_metrics" in unit_econ.json()

    policy = await client.post(
        "/api/v1/finops/policies/validate",
        json={
            "organization_slug": org,
            "policy_name": "guardrail-v1",
            "max_unverified_actions": 10,
            "min_confidence_score": 0.6,
            "max_risk_score": 0.9,
            "max_open_anomalies": 20,
            "required_fresh_sources": 1,
        },
    )
    assert policy.status_code == 200, policy.text
    assert "passed" in policy.json()

    narrative = await client.get("/api/v1/finops/executive/narrative", params={"organization_slug": org})
    assert narrative.status_code == 200, narrative.text
    assert "narrative_markdown" in narrative.json()
