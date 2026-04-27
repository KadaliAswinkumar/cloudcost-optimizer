"""
Infrastructure Intelligence API — organizations, connectors, scans, findings, reports, alerts.
"""

from __future__ import annotations

import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_db
from src.core.field_encryption import encrypt_string
from src.models.infra_intelligence import (
    AlertRule,
    CloudConnector,
    InfraFinding,
    InfraReport,
    Organization,
    ScanJob,
)
from src.schemas.infra_intelligence import (
    AlertRuleCreate,
    AlertRuleOut,
    ConnectorCreate,
    ConnectorOut,
    FindingOut,
    OrganizationCreate,
    OrganizationOut,
    ReportCreate,
    ReportOut,
    ScanCreate,
    ScanJobOut,
)
from src.services.infra_intelligence.background_scan import schedule_scan_job
from src.services.infra_intelligence.scan_service import run_scan_job
from src.services.infra_intelligence.report_builder import build_report_summary

router = APIRouter(prefix="/intelligence", tags=["Infrastructure Intelligence"])


async def _load_report(
    org_id: str,
    report_id: str,
    db: AsyncSession,
) -> InfraReport:
    await _get_org(db, org_id)
    res = await db.execute(
        select(InfraReport).where(
            InfraReport.id == report_id,
            InfraReport.organization_id == org_id,
        )
    )
    report = res.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="report not found")
    return report


async def _get_org(session: AsyncSession, org_id: str) -> Organization:
    res = await session.execute(select(Organization).where(Organization.id == org_id))
    org = res.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="organization not found")
    return org


@router.post("/organizations", response_model=OrganizationOut)
async def create_organization(
    body: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
) -> Organization:
    existing = await db.execute(select(Organization).where(Organization.slug == body.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="slug already exists")
    org = Organization(name=body.name, slug=body.slug)
    db.add(org)
    await db.flush()
    await db.refresh(org)
    return org


@router.get("/organizations", response_model=List[OrganizationOut])
async def list_organizations(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
) -> List[Organization]:
    res = await db.execute(select(Organization).order_by(Organization.created_at.desc()).limit(limit))
    return list(res.scalars().all())


@router.get("/organizations/{org_id}", response_model=OrganizationOut)
async def get_organization(
    org_id: str,
    db: AsyncSession = Depends(get_db),
) -> Organization:
    return await _get_org(db, org_id)


@router.post("/organizations/{org_id}/connectors", response_model=ConnectorOut)
async def create_connector(
    org_id: str,
    body: ConnectorCreate,
    db: AsyncSession = Depends(get_db),
) -> CloudConnector:
    await _get_org(db, org_id)
    try:
        creds = encrypt_string(json.dumps(body.credentials))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"credential encryption failed: {exc}") from exc
    conn = CloudConnector(
        organization_id=org_id,
        provider=body.provider,
        display_name=body.display_name,
        credentials_ciphertext=creds,
        status="active",
    )
    db.add(conn)
    await db.flush()
    await db.refresh(conn)
    return conn


@router.get("/organizations/{org_id}/connectors", response_model=List[ConnectorOut])
async def list_connectors(
    org_id: str,
    db: AsyncSession = Depends(get_db),
) -> List[CloudConnector]:
    await _get_org(db, org_id)
    res = await db.execute(
        select(CloudConnector)
        .where(CloudConnector.organization_id == org_id)
        .order_by(CloudConnector.created_at.desc())
    )
    return list(res.scalars().all())


@router.post(
    "/organizations/{org_id}/connectors/{connector_id}/scans",
    response_model=ScanJobOut,
    status_code=202,
)
async def trigger_scan(
    org_id: str,
    connector_id: str,
    body: ScanCreate,
    db: AsyncSession = Depends(get_db),
) -> ScanJob:
    await _get_org(db, org_id)
    cres = await db.execute(
        select(CloudConnector).where(
            CloudConnector.id == connector_id,
            CloudConnector.organization_id == org_id,
        )
    )
    connector = cres.scalar_one_or_none()
    if not connector:
        raise HTTPException(status_code=404, detail="connector not found")

    job = ScanJob(
        organization_id=org_id,
        cloud_connector_id=connector_id,
        status="pending",
        trigger=body.trigger,
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)
    job_id = job.id

    if settings.intelligence_scan_synchronous:
        # Same DB session as the request (required for tests that override get_db with SQLite).
        await run_scan_job(db, job_id)
    else:
        await db.commit()
        schedule_scan_job(job_id)

    res = await db.execute(select(ScanJob).where(ScanJob.id == job_id))
    return res.scalar_one()


@router.get("/organizations/{org_id}/scans", response_model=List[ScanJobOut])
async def list_scans(
    org_id: str,
    db: AsyncSession = Depends(get_db),
    connector_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
) -> List[ScanJob]:
    await _get_org(db, org_id)
    q = select(ScanJob).where(ScanJob.organization_id == org_id)
    if connector_id:
        q = q.where(ScanJob.cloud_connector_id == connector_id)
    q = q.order_by(ScanJob.created_at.desc()).limit(limit)
    res = await db.execute(q)
    return list(res.scalars().all())


@router.get("/organizations/{org_id}/scans/{scan_id}", response_model=ScanJobOut)
async def get_scan(
    org_id: str,
    scan_id: str,
    db: AsyncSession = Depends(get_db),
) -> ScanJob:
    await _get_org(db, org_id)
    res = await db.execute(
        select(ScanJob).where(
            ScanJob.id == scan_id,
            ScanJob.organization_id == org_id,
        )
    )
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="scan not found")
    return job


@router.get("/organizations/{org_id}/findings", response_model=List[FindingOut])
async def list_findings(
    org_id: str,
    db: AsyncSession = Depends(get_db),
    scan_id: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
) -> List[InfraFinding]:
    await _get_org(db, org_id)
    q = select(InfraFinding).where(InfraFinding.organization_id == org_id)
    if scan_id:
        q = q.where(InfraFinding.scan_job_id == scan_id)
    if category:
        q = q.where(InfraFinding.category == category)
    q = q.order_by(InfraFinding.created_at.desc()).limit(limit)
    res = await db.execute(q)
    return list(res.scalars().all())


@router.post("/organizations/{org_id}/reports", response_model=ReportOut)
async def create_report(
    org_id: str,
    body: ReportCreate,
    db: AsyncSession = Depends(get_db),
) -> InfraReport:
    await _get_org(db, org_id)
    if not body.scan_job_ids:
        raise HTTPException(status_code=400, detail="scan_job_ids must not be empty")

    res = await db.execute(
        select(InfraFinding).where(
            InfraFinding.organization_id == org_id,
            InfraFinding.scan_job_id.in_(body.scan_job_ids),
        )
    )
    rows = list(res.scalars().all())
    payload = [
        {
            "id": f.id,
            "severity": f.severity,
            "category": f.category,
            "title": f.title,
            "description": f.description,
            "estimated_monthly_savings": str(f.estimated_monthly_savings)
            if f.estimated_monthly_savings is not None
            else None,
            "rule_id": f.rule_id,
        }
        for f in rows
    ]
    summary = build_report_summary(
        title=body.title,
        scan_job_ids=body.scan_job_ids,
        findings_payload=payload,
    )
    report = InfraReport(organization_id=org_id, title=body.title, summary_json=summary)
    db.add(report)
    await db.flush()
    await db.refresh(report)
    return report


@router.get("/organizations/{org_id}/reports/{report_id}", response_model=ReportOut)
async def get_report(
    org_id: str,
    report_id: str,
    db: AsyncSession = Depends(get_db),
) -> InfraReport:
    return await _load_report(org_id, report_id, db)


@router.get("/organizations/{org_id}/reports/{report_id}/export")
async def export_report_json(
    org_id: str,
    report_id: str,
    db: AsyncSession = Depends(get_db),
) -> Response:
    report = await _load_report(org_id, report_id, db)
    body = json.dumps(jsonable_encoder(report.summary_json), indent=2)
    return Response(
        content=body,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="infra-report-{report_id}.json"',
        },
    )


@router.post("/organizations/{org_id}/alert-rules", response_model=AlertRuleOut)
async def create_alert_rule(
    org_id: str,
    body: AlertRuleCreate,
    db: AsyncSession = Depends(get_db),
) -> AlertRule:
    await _get_org(db, org_id)
    rule = AlertRule(
        organization_id=org_id,
        name=body.name,
        enabled=body.enabled,
        condition_json=body.condition_json,
        channel_json=body.channel_json,
    )
    db.add(rule)
    await db.flush()
    await db.refresh(rule)
    return rule


@router.get("/organizations/{org_id}/alert-rules", response_model=List[AlertRuleOut])
async def list_alert_rules(
    org_id: str,
    db: AsyncSession = Depends(get_db),
) -> List[AlertRule]:
    await _get_org(db, org_id)
    res = await db.execute(
        select(AlertRule)
        .where(AlertRule.organization_id == org_id)
        .order_by(AlertRule.created_at.desc())
    )
    return list(res.scalars().all())
