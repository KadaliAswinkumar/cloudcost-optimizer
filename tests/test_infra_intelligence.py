"""Tests for Infrastructure Intelligence API."""

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_intelligence_scan_findings_report(client: AsyncClient) -> None:
    slug = f"acme-{uuid.uuid4().hex[:8]}"
    r = await client.post(
        "/api/v1/intelligence/organizations",
        json={"name": "Acme Test", "slug": slug},
    )
    assert r.status_code == 200, r.text
    org = r.json()
    org_id = org["id"]

    r2 = await client.post(
        f"/api/v1/intelligence/organizations/{org_id}/connectors",
        json={
            "provider": "aws",
            "display_name": "Primary",
            "credentials": {"note": "stub — real collectors use role keys"},
        },
    )
    assert r2.status_code == 200, r2.text
    connector_id = r2.json()["id"]

    r3 = await client.post(
        f"/api/v1/intelligence/organizations/{org_id}/connectors/{connector_id}/scans",
        json={"trigger": "manual"},
    )
    assert r3.status_code == 200, r3.text
    scan = r3.json()
    assert scan["status"] == "completed"
    scan_id = scan["id"]

    r4 = await client.get(
        f"/api/v1/intelligence/organizations/{org_id}/findings",
        params={"scan_id": scan_id},
    )
    assert r4.status_code == 200, r4.text
    findings = r4.json()
    assert len(findings) >= 3
    categories = {f["category"] for f in findings}
    assert "cost" in categories
    assert "security" in categories
    assert "architecture" in categories

    r5 = await client.post(
        f"/api/v1/intelligence/organizations/{org_id}/reports",
        json={"title": "Executive summary", "scan_job_ids": [scan_id]},
    )
    assert r5.status_code == 200, r5.text
    report = r5.json()
    assert report["summary_json"]["finding_count"] == len(findings)

    r6 = await client.post(
        f"/api/v1/intelligence/organizations/{org_id}/alert-rules",
        json={
            "name": "High severity webhook",
            "enabled": True,
            "condition_json": {"min_severity": "high"},
            "channel_json": {"type": "webhook", "url": "https://example.com/hook"},
        },
    )
    assert r6.status_code == 200, r6.text
    r7 = await client.get(f"/api/v1/intelligence/organizations/{org_id}/alert-rules")
    assert r7.status_code == 200
    assert len(r7.json()) == 1
