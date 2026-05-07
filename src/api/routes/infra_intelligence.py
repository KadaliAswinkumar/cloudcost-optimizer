"""
Infrastructure Intelligence API — organizations, connectors, scans, findings, reports, alerts.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_db
from src.core.field_encryption import encrypt_string
from src.models.infra_intelligence import (
    AlertRule,
    AssetSnapshot,
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

_MISSING_INTEL_TABLES = (
    "Infrastructure Intelligence tables are not in this database yet. "
    "On the server run: alembic upgrade head (revision infra_intel_20260428 or later)."
)


def _intel_schema_missing(exc: BaseException) -> bool:
    msg = str(exc).lower()
    return (
        "no such table" in msg
        or ("relation" in msg and "does not exist" in msg)
        or "undefinedtable" in msg
    )


async def _intel_execute(session: AsyncSession, statement: Any):
    try:
        return await session.execute(statement)
    except (ProgrammingError, OperationalError) as exc:
        if _intel_schema_missing(exc):
            await session.rollback()
            raise HTTPException(status_code=503, detail=_MISSING_INTEL_TABLES) from exc
        raise


async def _intel_flush(session: AsyncSession) -> None:
    try:
        await session.flush()
    except (ProgrammingError, OperationalError) as exc:
        await session.rollback()
        if _intel_schema_missing(exc):
            raise HTTPException(status_code=503, detail=_MISSING_INTEL_TABLES) from exc
        raise


async def _load_report(
    org_id: str,
    report_id: str,
    db: AsyncSession,
) -> InfraReport:
    await _get_org(db, org_id)
    res = await _intel_execute(
        db,
        select(InfraReport).where(
            InfraReport.id == report_id,
            InfraReport.organization_id == org_id,
        ),
    )
    report = res.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="report not found")
    return report


async def _get_org(session: AsyncSession, org_id: str) -> Organization:
    res = await _intel_execute(session, select(Organization).where(Organization.id == org_id))
    org = res.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="organization not found")
    return org


async def _load_scan(session: AsyncSession, org_id: str, scan_id: str) -> ScanJob:
    res = await _intel_execute(
        session,
        select(ScanJob).where(
            ScanJob.id == scan_id,
            ScanJob.organization_id == org_id,
        ),
    )
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="scan not found")
    return job


async def _latest_snapshot_for_scan(session: AsyncSession, scan_id: str) -> AssetSnapshot:
    sres = await _intel_execute(
        session,
        select(AssetSnapshot)
        .where(AssetSnapshot.scan_job_id == scan_id)
        .order_by(AssetSnapshot.created_at.desc())
        .limit(1),
    )
    snap = sres.scalar_one_or_none()
    if not snap:
        raise HTTPException(status_code=404, detail="asset snapshot not found for scan")
    return snap


@router.post("/organizations", response_model=OrganizationOut)
async def create_organization(
    body: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
) -> Organization:
    existing = await _intel_execute(db, select(Organization).where(Organization.slug == body.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="slug already exists")
    org = Organization(name=body.name, slug=body.slug)
    db.add(org)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="slug already exists") from None
    except (ProgrammingError, OperationalError) as exc:
        await db.rollback()
        if _intel_schema_missing(exc):
            raise HTTPException(status_code=503, detail=_MISSING_INTEL_TABLES) from exc
        raise
    await db.refresh(org)
    return org


@router.get("/organizations", response_model=List[OrganizationOut])
async def list_organizations(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
) -> List[Organization]:
    res = await _intel_execute(db, select(Organization).order_by(Organization.created_at.desc()).limit(limit))
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
    await _intel_flush(db)
    await db.refresh(conn)
    return conn


@router.get("/organizations/{org_id}/connectors", response_model=List[ConnectorOut])
async def list_connectors(
    org_id: str,
    db: AsyncSession = Depends(get_db),
) -> List[CloudConnector]:
    await _get_org(db, org_id)
    res = await _intel_execute(
        db,
        select(CloudConnector)
        .where(CloudConnector.organization_id == org_id)
        .order_by(CloudConnector.created_at.desc()),
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
    cres = await _intel_execute(
        db,
        select(CloudConnector).where(
            CloudConnector.id == connector_id,
            CloudConnector.organization_id == org_id,
        ),
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
    await _intel_flush(db)
    await db.refresh(job)
    job_id = job.id

    if settings.intelligence_scan_synchronous:
        # Same DB session as the request (required for tests that override get_db with SQLite).
        await run_scan_job(db, job_id)
    else:
        await db.commit()
        schedule_scan_job(job_id)

    res = await _intel_execute(db, select(ScanJob).where(ScanJob.id == job_id))
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
    res = await _intel_execute(db, q)
    return list(res.scalars().all())


@router.get("/organizations/{org_id}/scans/{scan_id}", response_model=ScanJobOut)
async def get_scan(
    org_id: str,
    scan_id: str,
    db: AsyncSession = Depends(get_db),
) -> ScanJob:
    await _get_org(db, org_id)
    return await _load_scan(db, org_id, scan_id)


@router.get("/organizations/{org_id}/scans/{scan_id}/cost-summary")
async def get_scan_cost_summary(
    org_id: str,
    scan_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Return 30-day account-level cost summary captured during scan (when CE permissions exist).
    """
    await _get_org(db, org_id)
    await _load_scan(db, org_id, scan_id)
    snap = await _latest_snapshot_for_scan(db, scan_id)
    graph = snap.graph_json if isinstance(snap.graph_json, dict) else {}
    cost_summary = graph.get("cost_summary") if isinstance(graph.get("cost_summary"), dict) else {}
    if not cost_summary:
        raise HTTPException(
            status_code=404,
            detail=(
                "No cost summary found for this scan. Ensure connector IAM includes "
                "ce:GetCostAndUsage and rerun scan."
            ),
        )
    return {
        "scan_id": scan_id,
        "organization_id": org_id,
        "cost_summary": cost_summary,
        "collection_errors": graph.get("collection_errors") or [],
    }


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
    res = await _intel_execute(db, q)
    return list(res.scalars().all())


@router.get("/organizations/{org_id}/scans/{scan_id}/optimization-brief")
async def get_scan_optimization_brief(
    org_id: str,
    scan_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Build a practical optimization brief with savings target, top findings and user questions.
    """
    await _get_org(db, org_id)
    await _load_scan(db, org_id, scan_id)
    snap = await _latest_snapshot_for_scan(db, scan_id)
    graph = snap.graph_json if isinstance(snap.graph_json, dict) else {}
    cost_summary = graph.get("cost_summary") if isinstance(graph.get("cost_summary"), dict) else {}
    commitment_coverage = cost_summary.get("commitment_coverage") if isinstance(cost_summary, dict) else {}
    fs = await _intel_execute(
        db,
        select(InfraFinding).where(
            InfraFinding.organization_id == org_id,
            InfraFinding.scan_job_id == scan_id,
        ),
    )
    findings = list(fs.scalars().all())
    estimated = sum(float(f.estimated_monthly_savings or 0) for f in findings)
    high_cost = [f for f in findings if f.category == "cost" and f.severity in {"critical", "high"}]
    top = sorted(high_cost, key=lambda f: float(f.estimated_monthly_savings or 0), reverse=True)[:8]
    target_low = round(estimated * 0.45, 2)
    target_high = round(estimated * 0.72, 2)
    return {
        "scan_id": scan_id,
        "organization_id": org_id,
        "potential_monthly_savings_usd": round(estimated, 2),
        "target_savings_range_usd": {"low": target_low, "high": target_high},
        "target_savings_percent_guidance": "Typical practical range is 20-50%; 60-70% is possible only in heavily inefficient estates.",
        "commitment_coverage": commitment_coverage or {},
        "top_actions": [
            {
                "rule_id": f.rule_id,
                "title": f.title,
                "severity": f.severity,
                "estimated_monthly_savings_usd": float(f.estimated_monthly_savings or 0),
                "description": f.description,
            }
            for f in top
        ],
        "questions_to_ask_customer": [
            "Which workloads are production-critical vs interruptible (for Spot eligibility)?",
            "Do you already have Savings Plans/Reserved Instances and their coverage percentages?",
            "What SLO/SLA constraints prevent rightsizing or turning off resources?",
            "Can we access CUR/Cost Explorer with monthly granularity and tags for chargeback?",
            "Which EKS namespaces/services can run on Spot or scale to zero off-hours?",
        ],
    }


@router.post("/organizations/{org_id}/reports", response_model=ReportOut)
async def create_report(
    org_id: str,
    body: ReportCreate,
    db: AsyncSession = Depends(get_db),
) -> InfraReport:
    await _get_org(db, org_id)
    if not body.scan_job_ids:
        raise HTTPException(status_code=400, detail="scan_job_ids must not be empty")

    res = await _intel_execute(
        db,
        select(InfraFinding).where(
            InfraFinding.organization_id == org_id,
            InfraFinding.scan_job_id.in_(body.scan_job_ids),
        ),
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
    await _intel_flush(db)
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
    await _intel_flush(db)
    await db.refresh(rule)
    return rule


@router.get("/organizations/{org_id}/alert-rules", response_model=List[AlertRuleOut])
async def list_alert_rules(
    org_id: str,
    db: AsyncSession = Depends(get_db),
) -> List[AlertRule]:
    await _get_org(db, org_id)
    res = await _intel_execute(
        db,
        select(AlertRule)
        .where(AlertRule.organization_id == org_id)
        .order_by(AlertRule.created_at.desc()),
    )
    return list(res.scalars().all())
