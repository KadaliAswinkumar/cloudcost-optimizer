"""
FinOps & FOCUS-style cost dashboard API.

This route bundle powers traction-facing product features:
- Savings Command Center metrics (activation/impact/adoption)
- Recommendation lifecycle transitions (accept/implemented/dismiss)
- Onboarding source health (CSV/FOCUS, AWS CUR, Azure, GCP, API)
- Growth loops (weekly digest, leaderboard, what-if planner)
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from sqlalchemy import desc, func, select
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models.finops_traction import (
    FinOpsActionEvent,
    FinOpsAnomalyEvent,
    FinOpsIngestionSource,
    FinOpsRecommendationAction,
)

router = APIRouter(prefix="/finops", tags=["FinOps Dashboard"])

_MISSING_FINOPS_TABLES = (
    "FinOps traction tables are not in this database yet. "
    "Run migrations (or restart service so init_db create_all can register new tables)."
)


class FinOpsDashboardResponse(BaseModel):
    meta: Dict[str, Any]
    filters: Dict[str, Any]
    focus: Dict[str, Any]
    executive: Dict[str, Any]
    mom_trends: Dict[str, Any]
    activation: Dict[str, Any]
    impact: Dict[str, Any]
    adoption: Dict[str, Any]
    top_actions: List[Dict[str, Any]]


class RecommendationActionRequest(BaseModel):
    organization_slug: str = Field(..., min_length=2, max_length=80)
    actor: Optional[str] = Field(None, max_length=120)
    notes: Optional[str] = Field(None, max_length=2000)
    verification_notes: Optional[str] = Field(None, max_length=2000)
    rollback_reason: Optional[str] = Field(None, max_length=2000)
    realized_monthly_savings_usd: Optional[float] = Field(None, ge=0)


class IngestionSourceUpsertRequest(BaseModel):
    organization_slug: str = Field(..., min_length=2, max_length=80)
    source_type: Literal["csv_focus", "aws_cur", "azure_export", "gcp_billing", "api_push"]
    status: Literal["pending", "connected", "syncing", "error"] = "pending"
    freshness_status: Literal["fresh", "stale", "lagging", "unknown"] = "unknown"
    records_ingested: int = Field(0, ge=0)
    confidence_score: float = Field(0.7, ge=0, le=1)
    details_json: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = Field(None, max_length=4000)


class WhatIfPlannerRequest(BaseModel):
    organization_slug: str = Field(..., min_length=2, max_length=80)
    recommendation_ids: List[str] = Field(..., min_length=1)
    adoption_probability: float = Field(0.65, ge=0, le=1)


class AnomalyAcknowledgeRequest(BaseModel):
    organization_slug: str = Field(..., min_length=2, max_length=80)
    actor: Optional[str] = Field(None, max_length=120)


def _schema_missing(exc: BaseException) -> bool:
    msg = str(exc).lower()
    return (
        "no such table" in msg
        or ("relation" in msg and "does not exist" in msg)
        or "undefinedtable" in msg
    )


async def _finops_execute(session: AsyncSession, statement):
    try:
        return await session.execute(statement)
    except (ProgrammingError, OperationalError) as exc:
        if _schema_missing(exc):
            await session.rollback()
            raise HTTPException(status_code=503, detail=_MISSING_FINOPS_TABLES) from exc
        raise


async def _finops_flush(session: AsyncSession) -> None:
    try:
        await session.flush()
    except (ProgrammingError, OperationalError) as exc:
        await session.rollback()
        if _schema_missing(exc):
            raise HTTPException(status_code=503, detail=_MISSING_FINOPS_TABLES) from exc
        raise


def _confidence_level(score: float) -> str:
    if score >= 0.8:
        return "high"
    if score >= 0.6:
        return "medium"
    return "low"


def _decision_bucket(confidence: float, risk: float, savings: float) -> str:
    if confidence >= 0.78 and risk <= 0.45 and savings >= 250:
        return "do_first"
    if risk >= 0.7:
        return "review_manually"
    return "do_later"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _seed_actions(org_slug: str) -> List[FinOpsRecommendationAction]:
    now = datetime.utcnow()
    rows = [
        ("rec-ec2-rightsize-01", "Rightsize idle EC2 family from m5.2xlarge -> m6i.large", "aws", 1240.0, 0.91, "low"),
        ("rec-rds-storage-02", "Convert gp2 RDS storage to gp3 and lower provisioned IOPS", "aws", 890.0, 0.85, "medium"),
        ("rec-s3-tiering-03", "Enable S3 Intelligent-Tiering for inactive buckets", "aws", 540.0, 0.88, "low"),
        ("rec-azure-ri-04", "Purchase 1-year reserved capacity for steady Azure VM set", "azure", 2210.0, 0.79, "medium"),
        ("rec-gcp-commit-05", "Apply GCP committed use discounts to base node pools", "gcp", 1680.0, 0.83, "medium"),
        ("rec-egress-06", "Reduce inter-region data transfer by co-locating batch jobs", "aws", 760.0, 0.72, "high"),
        ("rec-nat-07", "Consolidate redundant NAT gateways in non-prod environments", "aws", 430.0, 0.76, "medium"),
        ("rec-k8s-08", "Tune Kubernetes requests/limits to unlock node scale-down", "azure", 1120.0, 0.82, "high"),
        ("rec-spot-09", "Shift fault-tolerant workers to Spot/Preemptible pools", "gcp", 980.0, 0.86, "medium"),
        ("rec-zombie-10", "Delete unattached EBS disks older than 30 days", "aws", 315.0, 0.93, "low"),
    ]
    seeded: List[FinOpsRecommendationAction] = []
    for rec_id, title, provider, savings, confidence, effort in rows:
        blast_radius = "low" if effort == "low" else ("medium" if effort == "medium" else "high")
        risk_score = 0.25 if blast_radius == "low" else (0.5 if blast_radius == "medium" else 0.78)
        seeded.append(
            FinOpsRecommendationAction(
                organization_slug=org_slug,
                recommendation_id=rec_id,
                title=title,
                cloud_provider=provider,
                status="open",
                estimated_monthly_savings_usd=Decimal(str(round(savings, 2))),
                confidence_score=confidence,
                confidence_level=_confidence_level(confidence),
                confidence_reasons_json={
                    "metrics_quality": "partial",
                    "cost_data_freshness": "fresh",
                    "tag_coverage": "medium",
                },
                effort_level=effort,
                risk_score=risk_score,
                blast_radius=blast_radius,
                decision_bucket=_decision_bucket(confidence, risk_score, savings),
                context_json={
                    "blast_radius": blast_radius,
                    "rollback": "Available",
                    "recommended_at": now.isoformat(),
                },
            )
        )
    return seeded


async def _ensure_seed_actions(session: AsyncSession, org_slug: str) -> None:
    count_res = await _finops_execute(
        session, select(func.count(FinOpsRecommendationAction.id)).where(FinOpsRecommendationAction.organization_slug == org_slug)
    )
    if (count_res.scalar() or 0) > 0:
        return
    for action in _seed_actions(org_slug):
        session.add(action)
    await _finops_flush(session)


async def _ensure_seed_sources(session: AsyncSession, org_slug: str) -> None:
    count_res = await _finops_execute(
        session, select(func.count(FinOpsIngestionSource.id)).where(FinOpsIngestionSource.organization_slug == org_slug)
    )
    if (count_res.scalar() or 0) > 0:
        return
    now = datetime.utcnow()
    starters = [
        ("csv_focus", "connected", "fresh", 14820, 0.94),
        ("aws_cur", "syncing", "lagging", 328742, 0.88),
        ("azure_export", "pending", "unknown", 0, 0.62),
        ("gcp_billing", "pending", "unknown", 0, 0.58),
        ("api_push", "connected", "fresh", 6402, 0.86),
    ]
    for source_type, status, freshness, records, confidence in starters:
        session.add(
            FinOpsIngestionSource(
                organization_slug=org_slug,
                source_type=source_type,
                status=status,
                freshness_status=freshness,
                records_ingested=records,
                confidence_score=confidence,
                details_json={"onboarding_path": source_type, "demo_seeded": True},
                last_synced_at=now if status in {"connected", "syncing"} else None,
            )
        )
    await _finops_flush(session)


async def _ensure_seed_anomalies(session: AsyncSession, org_slug: str) -> None:
    count_res = await _finops_execute(
        session, select(func.count(FinOpsAnomalyEvent.id)).where(FinOpsAnomalyEvent.organization_slug == org_slug)
    )
    if (count_res.scalar() or 0) > 0:
        return
    now = datetime.utcnow()
    session.add(
        FinOpsAnomalyEvent(
            organization_slug=org_slug,
            anomaly_type="spend_spike",
            severity="high",
            metric_name="daily_compute_cost_usd",
            baseline_value=Decimal("4200"),
            observed_value=Decimal("6900"),
            deviation_pct=64.29,
            details_json={"service": "ec2", "region": "ap-south-1"},
            detected_at=now - timedelta(hours=6),
        )
    )
    session.add(
        FinOpsAnomalyEvent(
            organization_slug=org_slug,
            anomaly_type="savings_regression",
            severity="medium",
            metric_name="realized_savings_7d_usd",
            baseline_value=Decimal("1800"),
            observed_value=Decimal("980"),
            deviation_pct=-45.56,
            details_json={"trigger": "recent workload scale-up"},
            detected_at=now - timedelta(days=1, hours=2),
        )
    )
    await _finops_flush(session)


async def _log_action_event(
    session: AsyncSession,
    *,
    organization_slug: str,
    recommendation_id: str,
    event_type: str,
    actor: Optional[str],
    payload: Dict[str, Any],
) -> None:
    session.add(
        FinOpsActionEvent(
            organization_slug=organization_slug,
            recommendation_id=recommendation_id,
            event_type=event_type,
            actor=actor,
            payload_json=payload,
        )
    )
    await _finops_flush(session)


async def _auto_detect_anomalies(session: AsyncSession, org_slug: str) -> None:
    """
    Detect simple spend/savings anomalies from recent action deltas.
    """
    now = datetime.utcnow()
    this_week_start = now - timedelta(days=7)
    prev_week_start = now - timedelta(days=14)

    this_week_res = await _finops_execute(
        session,
        select(func.sum(FinOpsRecommendationAction.realized_monthly_savings_usd)).where(
            FinOpsRecommendationAction.organization_slug == org_slug,
            FinOpsRecommendationAction.updated_at >= this_week_start,
        ),
    )
    prev_week_res = await _finops_execute(
        session,
        select(func.sum(FinOpsRecommendationAction.realized_monthly_savings_usd)).where(
            FinOpsRecommendationAction.organization_slug == org_slug,
            FinOpsRecommendationAction.updated_at >= prev_week_start,
            FinOpsRecommendationAction.updated_at < this_week_start,
        ),
    )
    this_week = float(this_week_res.scalar() or 0)
    prev_week = float(prev_week_res.scalar() or 0)

    # Savings regression anomaly
    if prev_week > 0:
        delta_pct = ((this_week - prev_week) / prev_week) * 100.0
        if delta_pct <= -25:
            existing = await _finops_execute(
                session,
                select(func.count(FinOpsAnomalyEvent.id)).where(
                    FinOpsAnomalyEvent.organization_slug == org_slug,
                    FinOpsAnomalyEvent.anomaly_type == "savings_regression",
                    FinOpsAnomalyEvent.status.in_(["open", "acknowledged"]),
                    FinOpsAnomalyEvent.detected_at >= now - timedelta(days=2),
                ),
            )
            if int(existing.scalar() or 0) == 0:
                session.add(
                    FinOpsAnomalyEvent(
                        organization_slug=org_slug,
                        anomaly_type="savings_regression",
                        severity="high" if delta_pct <= -40 else "medium",
                        metric_name="realized_savings_weekly_usd",
                        baseline_value=Decimal(str(round(prev_week, 2))),
                        observed_value=Decimal(str(round(this_week, 2))),
                        deviation_pct=round(delta_pct, 2),
                        details_json={"auto_detected": True, "window_days": 7},
                    )
                )

    # Spend pressure anomaly from open opportunity backlog
    rec_res = await _finops_execute(
        session,
        select(
            func.sum(FinOpsRecommendationAction.estimated_monthly_savings_usd).label("est"),
            func.sum(FinOpsRecommendationAction.realized_monthly_savings_usd).label("real"),
        ).where(FinOpsRecommendationAction.organization_slug == org_slug),
    )
    row = rec_res.one()
    est = float(row.est or 0)
    real = float(row.real or 0)
    gap = max(est - real, 0)
    if est > 0:
        gap_pct = (gap / est) * 100.0
        if gap_pct >= 55:
            existing2 = await _finops_execute(
                session,
                select(func.count(FinOpsAnomalyEvent.id)).where(
                    FinOpsAnomalyEvent.organization_slug == org_slug,
                    FinOpsAnomalyEvent.anomaly_type == "opportunity_backlog_high",
                    FinOpsAnomalyEvent.status.in_(["open", "acknowledged"]),
                    FinOpsAnomalyEvent.detected_at >= now - timedelta(days=2),
                ),
            )
            if int(existing2.scalar() or 0) == 0:
                session.add(
                    FinOpsAnomalyEvent(
                        organization_slug=org_slug,
                        anomaly_type="opportunity_backlog_high",
                        severity="medium",
                        metric_name="realized_vs_estimated_gap_usd",
                        baseline_value=Decimal(str(round(est, 2))),
                        observed_value=Decimal(str(round(real, 2))),
                        deviation_pct=round(-gap_pct, 2),
                        details_json={"auto_detected": True, "gap_usd": round(gap, 2)},
                    )
                )
    await _finops_flush(session)


async def _metrics_from_actions(
    session: AsyncSession, org_slug: str
) -> Dict[str, Any]:
    await _ensure_seed_actions(session, org_slug)
    await _ensure_seed_sources(session, org_slug)
    await _ensure_seed_anomalies(session, org_slug)

    actions_res = await _finops_execute(
        session,
        select(FinOpsRecommendationAction)
        .where(FinOpsRecommendationAction.organization_slug == org_slug)
        .order_by(
            FinOpsRecommendationAction.status.asc(),
            desc(FinOpsRecommendationAction.estimated_monthly_savings_usd),
        ),
    )
    actions = list(actions_res.scalars().all())
    now = datetime.utcnow()

    recommended = sum(float(a.estimated_monthly_savings_usd or 0) for a in actions if a.status != "dismissed")
    implemented = sum(
        float(a.estimated_monthly_savings_usd or 0)
        for a in actions
        if a.status in {"implemented", "verified"}
    )
    realized = sum(
        float(a.realized_monthly_savings_usd or 0)
        for a in actions
        if a.status in {"implemented", "verified"}
    )
    actioned = [a for a in actions if a.status in {"accepted", "in_progress", "implemented", "verified"}]
    actioned_recent = [a for a in actioned if a.updated_at and (now - a.updated_at).days <= 7]
    accept_rate = (len(actioned) / max(len([a for a in actions if a.status != "dismissed"]), 1)) * 100.0

    sources_res = await _finops_execute(
        session,
        select(FinOpsIngestionSource).where(FinOpsIngestionSource.organization_slug == org_slug),
    )
    sources = list(sources_res.scalars().all())
    connected_sources = [s for s in sources if s.status in {"connected", "syncing"}]
    fresh_sources = [s for s in sources if s.freshness_status == "fresh"]

    first_source_at = min((s.created_at for s in sources), default=None)
    first_action_at = min(
        (
            a.accepted_at or a.in_progress_at or a.implemented_at or a.verified_at
            for a in actioned
            if (a.accepted_at or a.in_progress_at or a.implemented_at or a.verified_at) is not None
        ),
        default=None,
    )
    ttfh = None
    if first_source_at and first_action_at:
        ttfh = round((first_action_at - first_source_at).total_seconds() / 3600.0, 2)

    weekly_org_res = await _finops_execute(
        session,
        select(func.count(func.distinct(FinOpsRecommendationAction.organization_slug))).where(
            FinOpsRecommendationAction.updated_at >= (now - timedelta(days=7))
        ),
    )
    weekly_active_orgs = int(weekly_org_res.scalar() or 0)

    top_actions: List[Dict[str, Any]] = []
    for a in actions[:10]:
        top_actions.append(
            {
                "recommendation_id": a.recommendation_id,
                "title": a.title,
                "cloud_provider": a.cloud_provider,
                "status": a.status,
                "confidence_score": float(a.confidence_score),
                "confidence_level": a.confidence_level,
                "confidence_reasons": a.confidence_reasons_json,
                "effort_level": a.effort_level,
                "risk_score": float(a.risk_score or 0),
                "blast_radius": a.blast_radius,
                "decision_bucket": a.decision_bucket,
                "estimated_monthly_savings_usd": float(a.estimated_monthly_savings_usd),
                "realized_monthly_savings_usd": float(a.realized_monthly_savings_usd or 0),
                "context": a.context_json,
                "updated_at": a.updated_at.isoformat() if a.updated_at else None,
            }
        )

    return {
        "activation": {
            "time_to_first_saving_hours": ttfh,
            "onboarding_step_completion": round((len(connected_sources) / max(len(sources), 1)) * 100.0, 2),
            "data_sources_connected": len(connected_sources),
            "fresh_sources": len(fresh_sources),
        },
        "impact": {
            "recommended_savings_usd": round(recommended, 2),
            "implemented_savings_usd": round(implemented, 2),
            "realized_savings_30d_usd": round(realized, 2),
            "actions_taken_usd": round(realized + implemented * 0.12, 2),
            "risk_adjusted_opportunity_usd": round(max(recommended - realized, 0) * 0.74, 2),
        },
        "adoption": {
            "weekly_active_orgs": weekly_active_orgs,
            "recommendation_accept_rate": round(accept_rate, 2),
            "repeat_scan_rate": round((len(actioned_recent) / max(len(actions), 1)) * 100.0, 2),
        },
        "top_actions": top_actions,
    }


def _demo_dashboard(
    *,
    team: str,
    provider_filter: Optional[str],
    cost_type: str,
) -> Dict[str, Any]:
    """Deterministic demo dataset; weights India regions for APAC relevance."""
    scale = 1.0
    if team and team not in ("All", "all", ""):
        scale = 0.92 + (hash(team) % 17) / 100.0

    months = [
        ("2024-08", "Aug 2024"),
        ("2024-09", "Sep 2024"),
        ("2024-10", "Oct 2024"),
        ("2024-11", "Nov 2024"),
    ]
    base_kpi = [159_960, 504_210, 480_550, 445_000]
    effective_by_month = []
    for i, (m, lab) in enumerate(months):
        amt = base_kpi[i] * scale
        effective_by_month.append({"month": m, "label": lab, "amount_usd": round(amt, 2)})

    # Region word cloud — emphasize India + common EU/US for global enterprises
    region_cloud: List[Dict[str, Any]] = [
        {"name": "Asia Pacific (Mumbai)", "weight": 0.38, "cost_usd": round(185_000 * scale)},
        {"name": "Asia Pacific (Hyderabad)", "weight": 0.28, "cost_usd": round(132_000 * scale)},
        {"name": "EU (Frankfurt)", "weight": 0.22, "cost_usd": round(98_000 * scale)},
        {"name": "EU (Ireland)", "weight": 0.20, "cost_usd": round(91_000 * scale)},
        {"name": "US East (N. Virginia)", "weight": 0.18, "cost_usd": round(84_000 * scale)},
        {"name": "Asia Pacific (Singapore)", "weight": 0.15, "cost_usd": round(72_000 * scale)},
    ]

    services = ["ec2", "eks", "rds", "s3", "opensearch", "guardduty", "other"]
    cost_by_service_monthly = []
    for i, (m, lab) in enumerate(months):
        row: Dict[str, Any] = {"month": m, "month_label": lab}
        seed = 120_000 + i * 35_000
        for j, s in enumerate(services):
            row[s] = round((seed * (0.28 - j * 0.03)) * scale * (1.05 if provider_filter == "aws" else 1.0))
        cost_by_service_monthly.append(row)

    cost_by_provider_monthly = []
    for i, (m, lab) in enumerate(months):
        aws_v = round((280_000 + i * 40_000) * scale)
        azure_v = round((190_000 + i * 22_000) * scale)
        row = {"month": m, "month_label": lab, "Amazon Web Services": aws_v, "Microsoft Azure": azure_v}
        if not provider_filter:
            pass
        elif provider_filter.lower() == "aws":
            row = {"month": m, "month_label": lab, "Amazon Web Services": aws_v}
        elif provider_filter.lower() in ("azure", "microsoft"):
            row = {"month": m, "month_label": lab, "Microsoft Azure": azure_v}
        cost_by_provider_monthly.append(row)

    # Sankey: Provider -> Service category
    nodes = [
        {"name": "AWS"},
        {"name": "Microsoft"},
        {"name": "Compute"},
        {"name": "Storage"},
        {"name": "Databases"},
        {"name": "Networking"},
        {"name": "Security"},
        {"name": "Management"},
    ]
    links = [
        {"source": 0, "target": 2, "value": round(420_000 * scale)},
        {"source": 0, "target": 3, "value": round(180_000 * scale)},
        {"source": 0, "target": 4, "value": round(95_000 * scale)},
        {"source": 0, "target": 5, "value": round(88_000 * scale)},
        {"source": 0, "target": 6, "value": round(62_000 * scale)},
        {"source": 1, "target": 2, "value": round(310_000 * scale)},
        {"source": 1, "target": 3, "value": round(140_000 * scale)},
        {"source": 1, "target": 4, "value": round(78_000 * scale)},
        {"source": 1, "target": 7, "value": round(55_000 * scale)},
    ]

    cats = ["Compute", "Storage", "Databases", "AIML", "Analytics", "Networking", "Security"]
    sub_accounts = [
        ("prod-in-ap-south-1", 0.35),
        ("platform-hyderabad", 0.22),
        ("shared-services", 0.18),
        ("data-lake-mumbai", 0.15),
        ("sandbox-eu", 0.10),
    ]
    sub_account_bars = []
    for name, w in sub_accounts:
        row: Dict[str, Any] = {"name": name}
        total = 0.0
        for j, c in enumerate(cats):
            v = round(900_000 * w * (0.35 - j * 0.04) * scale)
            row[c.lower().replace(" ", "_")] = v
            total += v
        row["total_usd"] = round(total)
        sub_account_bars.append(row)

    executive = {
        "teams": [
            "All",
            "Team: Auditing",
            "Team: Buzz Logic",
            "Team: CCOE",
            "Team: Data Science",
            "Team: Morphius",
        ],
        "spend_ytd_amortized_usd": round(103_158_456.52 * scale, 2),
        "spend_ytd_cash_usd": round(98_762_568.77 * scale, 2),
        "monthly_estimated": {
            "current_amortized_usd": round(11_193_068.47 * scale, 2),
            "previous_amortized_usd": round(12_802_874.38 * scale, 2),
        },
        "vendor_pie": [
            {"name": "Azure", "percent": 47.1, "amount_usd": round(4_900_000 * scale)},
            {"name": "Amazon", "percent": 34.4, "amount_usd": round(3_600_000 * scale)},
            {"name": "GCP", "percent": 4.9, "amount_usd": round(510_000 * scale)},
            {"name": "OCI", "percent": 12.3, "amount_usd": round(1_280_000 * scale)},
            {"name": "IBM", "percent": 1.3, "amount_usd": round(135_000 * scale)},
        ],
        "cost_center_pie": [
            {"name": "Engineering", "percent": 38.0},
            {"name": "Data & AI", "percent": 22.0},
            {"name": "Media", "percent": 18.0},
            {"name": "Shared", "percent": 14.0},
            {"name": "Unallocated", "percent": 8.0},
        ],
        "daily_by_usage_family": _daily_usage_family(scale),
        "chargeback_table": [
            {
                "cost_center": "media",
                "business_unit": "digital",
                "application": "web",
                "allocation_driver": "application resource tag",
                "cost_amortized_usd": round(1_820_000 * scale),
            },
            {
                "cost_center": "unallocated",
                "business_unit": "unknown",
                "application": "testnox",
                "allocation_driver": "azure subscription",
                "cost_amortized_usd": round(980_000 * scale),
            },
            {
                "cost_center": "platform",
                "business_unit": "television",
                "application": "content manager",
                "allocation_driver": "application resource tag",
                "cost_amortized_usd": round(1_240_000 * scale),
            },
        ],
    }

    mom_series = []
    for i, (m, lab) in enumerate(months):
        t = round((410_000 + i * 45_000) * scale)
        mom_series.append(
            {
                "month": m,
                "label": lab,
                "total_usd": t,
                "aws_usd": round(t * 0.58),
                "azure_usd": round(t * 0.34),
                "gcp_usd": round(t * 0.08),
            }
        )

    return {
        "meta": {
            "data_mode": "demo",
            "focus_aligned": True,
            "currency": "USD",
            "cost_type_requested": cost_type,
            "team_filter": team or "All",
            "updated_at": _now_iso(),
            "notes": (
                "Demo dataset for UI/UX; replace with CUR / FOCUS exports / billing APIs when connectors are configured. "
                "India regions (Mumbai, Hyderabad) weighted for APAC showcase."
            ),
        },
        "filters": {
            "providers": ["", "aws", "azure", "gcp"],
            "teams": executive["teams"],
            "cost_types": ["effective", "amortized", "cash"],
            "charge_categories": ["Usage", "Purchase", "Tax", "Credit"],
        },
        "focus": {
            "kpis": {
                "effective_cost_by_month": effective_by_month,
                "total_accounts": 481,
                "total_services": 178,
                "total_providers": 2 if not provider_filter else 1,
            },
            "region_word_cloud": region_cloud,
            "cost_by_service_monthly": cost_by_service_monthly,
            "service_keys": services,
            "cost_by_provider_monthly": cost_by_provider_monthly,
            "group_by_options": [
                "billing_account",
                "charge_category",
                "provider",
                "service_category",
                "sub_account",
            ],
            "sankey": {"nodes": nodes, "links": links},
            "sub_account_bars": sub_account_bars,
            "sub_account_category_keys": [c.lower().replace(" ", "_") for c in cats],
        },
        "executive": executive,
        "mom_trends": {"series": mom_series},
    }


def _daily_usage_family(scale: float) -> List[Dict[str, Any]]:
    families = [
        "Instance Usage",
        "Storage",
        "Data Transfer",
        "Database Units",
        "Network",
        "Security",
        "Other",
    ]
    out: List[Dict[str, Any]] = []
    for d in range(1, 31):
        row: Dict[str, Any] = {"day": f"2024-08-{d:02d}", "label": f"Aug {d}"}
        base = 12_000 + (d % 7) * 800
        for j, f in enumerate(families):
            row[f] = round(base * (0.35 - j * 0.04) * scale)
        out.append(row)
    return out


@router.get("/dashboard", response_model=FinOpsDashboardResponse)
async def get_finops_dashboard(
    team: str = Query("All", description="Shared view / chargeback team"),
    organization_slug: str = Query("global", description="Tenant slug for traction metrics"),
    provider: Optional[str] = Query(None, description="Optional: aws | azure | gcp"),
    cost_type: Literal["effective", "amortized", "cash"] = Query(
        "effective",
        description="Reporting basis (demo adjusts labels only until live data)",
    ),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Aggregated FinOps dashboard payload (FOCUS-inspired + executive curated widgets).

    **Demo mode:** safe for production UI shell; swap backend source when billing exports are linked.
    """
    base = _demo_dashboard(team=team, provider_filter=provider, cost_type=cost_type)
    traction = await _metrics_from_actions(db, organization_slug)
    base.update(traction)
    return base


async def _get_action_or_404(
    db: AsyncSession, organization_slug: str, recommendation_id: str
) -> FinOpsRecommendationAction:
    res = await _finops_execute(
        db,
        select(FinOpsRecommendationAction).where(
            FinOpsRecommendationAction.organization_slug == organization_slug,
            FinOpsRecommendationAction.recommendation_id == recommendation_id,
        ),
    )
    action = res.scalar_one_or_none()
    if action:
        return action
    await _ensure_seed_actions(db, organization_slug)
    res = await _finops_execute(
        db,
        select(FinOpsRecommendationAction).where(
            FinOpsRecommendationAction.organization_slug == organization_slug,
            FinOpsRecommendationAction.recommendation_id == recommendation_id,
        ),
    )
    action = res.scalar_one_or_none()
    if not action:
        raise HTTPException(status_code=404, detail="recommendation not found")
    return action


@router.get("/recommendations")
async def list_recommendation_actions(
    organization_slug: str = Query(..., description="Tenant slug"),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    metrics = await _metrics_from_actions(db, organization_slug)
    return {
        "organization_slug": organization_slug,
        "top_actions": metrics["top_actions"],
        "impact": metrics["impact"],
        "adoption": metrics["adoption"],
    }


@router.post("/recommendations/{recommendation_id}/accept")
async def accept_recommendation(
    recommendation_id: str,
    body: RecommendationActionRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    action = await _get_action_or_404(db, body.organization_slug, recommendation_id)
    action.status = "accepted"
    action.accepted_at = datetime.utcnow()
    action.actioned_by = body.actor or action.actioned_by
    action.notes = body.notes or action.notes
    await _finops_flush(db)
    await _log_action_event(
        db,
        organization_slug=body.organization_slug,
        recommendation_id=action.recommendation_id,
        event_type="accepted",
        actor=body.actor,
        payload={"notes": body.notes},
    )
    return {"ok": True, "status": action.status, "recommendation_id": action.recommendation_id}


@router.post("/recommendations/{recommendation_id}/implemented")
async def implement_recommendation(
    recommendation_id: str,
    body: RecommendationActionRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    action = await _get_action_or_404(db, body.organization_slug, recommendation_id)
    action.status = "implemented"
    now = datetime.utcnow()
    action.accepted_at = action.accepted_at or now
    action.implemented_at = now
    action.actioned_by = body.actor or action.actioned_by
    action.notes = body.notes or action.notes
    realized = body.realized_monthly_savings_usd
    if realized is None:
        realized = float(action.estimated_monthly_savings_usd) * 0.82
    action.realized_monthly_savings_usd = Decimal(str(round(realized, 2)))
    await _finops_flush(db)
    await _log_action_event(
        db,
        organization_slug=body.organization_slug,
        recommendation_id=action.recommendation_id,
        event_type="implemented",
        actor=body.actor,
        payload={"realized_monthly_savings_usd": realized, "notes": body.notes},
    )
    return {"ok": True, "status": action.status, "recommendation_id": action.recommendation_id}


@router.post("/recommendations/{recommendation_id}/in-progress")
async def mark_recommendation_in_progress(
    recommendation_id: str,
    body: RecommendationActionRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    action = await _get_action_or_404(db, body.organization_slug, recommendation_id)
    action.status = "in_progress"
    now = datetime.utcnow()
    action.accepted_at = action.accepted_at or now
    action.in_progress_at = now
    action.actioned_by = body.actor or action.actioned_by
    action.notes = body.notes or action.notes
    await _finops_flush(db)
    await _log_action_event(
        db,
        organization_slug=body.organization_slug,
        recommendation_id=action.recommendation_id,
        event_type="in_progress",
        actor=body.actor,
        payload={"notes": body.notes},
    )
    return {"ok": True, "status": action.status, "recommendation_id": action.recommendation_id}


@router.post("/recommendations/{recommendation_id}/verify")
async def verify_recommendation(
    recommendation_id: str,
    body: RecommendationActionRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    action = await _get_action_or_404(db, body.organization_slug, recommendation_id)
    now = datetime.utcnow()
    action.status = "verified"
    action.accepted_at = action.accepted_at or now
    action.in_progress_at = action.in_progress_at or action.implemented_at or now
    action.implemented_at = action.implemented_at or now
    action.verified_at = now
    action.actioned_by = body.actor or action.actioned_by
    action.verification_notes = body.verification_notes or body.notes or action.verification_notes
    realized = body.realized_monthly_savings_usd
    if realized is not None:
        action.realized_monthly_savings_usd = Decimal(str(round(realized, 2)))
    await _finops_flush(db)
    await _log_action_event(
        db,
        organization_slug=body.organization_slug,
        recommendation_id=action.recommendation_id,
        event_type="verified",
        actor=body.actor,
        payload={
            "verification_notes": body.verification_notes or body.notes,
            "realized_monthly_savings_usd": float(action.realized_monthly_savings_usd or 0),
        },
    )
    return {"ok": True, "status": action.status, "recommendation_id": action.recommendation_id}


@router.post("/recommendations/{recommendation_id}/rollback")
async def rollback_recommendation(
    recommendation_id: str,
    body: RecommendationActionRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    action = await _get_action_or_404(db, body.organization_slug, recommendation_id)
    now = datetime.utcnow()
    action.status = "accepted"
    action.rolled_back_at = now
    action.rollback_reason = body.rollback_reason or body.notes or action.rollback_reason
    action.verification_notes = body.verification_notes or action.verification_notes
    action.actioned_by = body.actor or action.actioned_by
    await _finops_flush(db)
    await _log_action_event(
        db,
        organization_slug=body.organization_slug,
        recommendation_id=action.recommendation_id,
        event_type="rolled_back",
        actor=body.actor,
        payload={"rollback_reason": action.rollback_reason, "notes": body.notes},
    )
    return {"ok": True, "status": action.status, "recommendation_id": action.recommendation_id}


@router.post("/recommendations/{recommendation_id}/dismiss")
async def dismiss_recommendation(
    recommendation_id: str,
    body: RecommendationActionRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    action = await _get_action_or_404(db, body.organization_slug, recommendation_id)
    action.status = "dismissed"
    action.dismissed_at = datetime.utcnow()
    action.actioned_by = body.actor or action.actioned_by
    action.notes = body.notes or action.notes
    await _finops_flush(db)
    await _log_action_event(
        db,
        organization_slug=body.organization_slug,
        recommendation_id=action.recommendation_id,
        event_type="dismissed",
        actor=body.actor,
        payload={"notes": body.notes},
    )
    return {"ok": True, "status": action.status, "recommendation_id": action.recommendation_id}


@router.get("/onboarding/sources")
async def list_ingestion_sources(
    organization_slug: str = Query(..., description="Tenant slug"),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    await _ensure_seed_sources(db, organization_slug)
    res = await _finops_execute(
        db,
        select(FinOpsIngestionSource)
        .where(FinOpsIngestionSource.organization_slug == organization_slug)
        .order_by(FinOpsIngestionSource.source_type.asc()),
    )
    sources = []
    for s in res.scalars().all():
        sources.append(
            {
                "id": s.id,
                "source_type": s.source_type,
                "status": s.status,
                "freshness_status": s.freshness_status,
                "records_ingested": s.records_ingested,
                "confidence_score": float(s.confidence_score),
                "details_json": s.details_json,
                "error_message": s.error_message,
                "last_synced_at": s.last_synced_at.isoformat() if s.last_synced_at else None,
            }
        )
    return {"organization_slug": organization_slug, "sources": sources}


@router.post("/onboarding/sources")
async def upsert_ingestion_source(
    body: IngestionSourceUpsertRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    res = await _finops_execute(
        db,
        select(FinOpsIngestionSource).where(
            FinOpsIngestionSource.organization_slug == body.organization_slug,
            FinOpsIngestionSource.source_type == body.source_type,
        ),
    )
    source = res.scalar_one_or_none()
    if not source:
        source = FinOpsIngestionSource(
            organization_slug=body.organization_slug,
            source_type=body.source_type,
        )
        db.add(source)
    source.status = body.status
    source.freshness_status = body.freshness_status
    source.records_ingested = body.records_ingested
    source.confidence_score = body.confidence_score
    source.details_json = body.details_json
    source.error_message = body.error_message
    source.last_synced_at = datetime.utcnow() if body.status in {"connected", "syncing"} else None
    await _finops_flush(db)
    return {"ok": True, "source_type": source.source_type, "status": source.status}


@router.get("/onboarding/health")
async def onboarding_health(
    organization_slug: str = Query(..., description="Tenant slug"),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    payload = await list_ingestion_sources(organization_slug, db)
    sources = payload["sources"]
    connected = len([s for s in sources if s["status"] in {"connected", "syncing"}])
    fresh = len([s for s in sources if s["freshness_status"] == "fresh"])
    confidence = (
        round(sum(float(s["confidence_score"]) for s in sources) / len(sources), 3) if sources else 0
    )
    return {
        "organization_slug": organization_slug,
        "summary": {
            "total_sources": len(sources),
            "connected_sources": connected,
            "fresh_sources": fresh,
            "data_freshness_confidence": confidence,
        },
        "sources": sources,
    }


@router.get("/growth/leaderboard")
async def growth_leaderboard(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    res = await _finops_execute(
        db,
        select(
            FinOpsRecommendationAction.organization_slug,
            func.sum(FinOpsRecommendationAction.realized_monthly_savings_usd).label("realized"),
            func.sum(FinOpsRecommendationAction.estimated_monthly_savings_usd).label("estimated"),
            func.count(FinOpsRecommendationAction.id).label("actions"),
        )
        .group_by(FinOpsRecommendationAction.organization_slug)
        .order_by(desc("realized"))
        .limit(limit),
    )
    rows = []
    for r in res.all():
        realized = float(r.realized or 0)
        estimated = float(r.estimated or 0)
        rows.append(
            {
                "organization_slug": r.organization_slug,
                "realized_monthly_savings_usd": round(realized, 2),
                "estimated_monthly_savings_usd": round(estimated, 2),
                "realization_rate": round((realized / estimated) * 100.0, 2) if estimated else 0,
                "actions_count": int(r.actions or 0),
            }
        )
    return {"leaderboard": rows}


@router.get("/growth/weekly-digest")
async def weekly_digest(
    organization_slug: str = Query(..., description="Tenant slug"),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    metrics = await _metrics_from_actions(db, organization_slug)
    since = datetime.utcnow() - timedelta(days=7)
    res = await _finops_execute(
        db,
        select(FinOpsRecommendationAction)
        .where(
            FinOpsRecommendationAction.organization_slug == organization_slug,
            FinOpsRecommendationAction.updated_at >= since,
        )
        .order_by(desc(FinOpsRecommendationAction.updated_at)),
    )
    changes = []
    for row in res.scalars().all():
        changes.append(
            {
                "recommendation_id": row.recommendation_id,
                "title": row.title,
                "status": row.status,
                "estimated_monthly_savings_usd": float(row.estimated_monthly_savings_usd),
                "realized_monthly_savings_usd": float(row.realized_monthly_savings_usd or 0),
                "updated_at": row.updated_at.isoformat() if row.updated_at else None,
            }
        )
    return {
        "organization_slug": organization_slug,
        "period_days": 7,
        "impact_summary": metrics["impact"],
        "adoption_summary": metrics["adoption"],
        "changes": changes,
        "next_best_actions": metrics["top_actions"][:3],
    }


@router.get("/anomalies")
async def list_anomalies(
    organization_slug: str = Query(..., description="Tenant slug"),
    include_resolved: bool = Query(False),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    await _ensure_seed_anomalies(db, organization_slug)
    await _auto_detect_anomalies(db, organization_slug)
    q = select(FinOpsAnomalyEvent).where(FinOpsAnomalyEvent.organization_slug == organization_slug)
    if not include_resolved:
        q = q.where(FinOpsAnomalyEvent.status != "resolved")
    q = q.order_by(desc(FinOpsAnomalyEvent.detected_at))
    res = await _finops_execute(db, q)
    anomalies = [
        {
            "id": a.id,
            "anomaly_type": a.anomaly_type,
            "severity": a.severity,
            "status": a.status,
            "metric_name": a.metric_name,
            "baseline_value": float(a.baseline_value or 0),
            "observed_value": float(a.observed_value or 0),
            "deviation_pct": float(a.deviation_pct or 0),
            "details": a.details_json,
            "detected_at": a.detected_at.isoformat() if a.detected_at else None,
        }
        for a in res.scalars().all()
    ]
    return {"organization_slug": organization_slug, "anomalies": anomalies}


@router.post("/anomalies/{anomaly_id}/acknowledge")
async def acknowledge_anomaly(
    anomaly_id: str,
    body: AnomalyAcknowledgeRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    res = await _finops_execute(
        db,
        select(FinOpsAnomalyEvent).where(
            FinOpsAnomalyEvent.id == anomaly_id,
            FinOpsAnomalyEvent.organization_slug == body.organization_slug,
        ),
    )
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="anomaly not found")
    row.status = "acknowledged"
    await _finops_flush(db)
    return {"ok": True, "anomaly_id": anomaly_id, "status": row.status}


@router.post("/growth/what-if")
async def what_if_planner(
    body: WhatIfPlannerRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    res = await _finops_execute(
        db,
        select(FinOpsRecommendationAction).where(
            FinOpsRecommendationAction.organization_slug == body.organization_slug,
            FinOpsRecommendationAction.recommendation_id.in_(body.recommendation_ids),
        ),
    )
    rows = list(res.scalars().all())
    if not rows:
        raise HTTPException(status_code=404, detail="no matching recommendations found")
    gross = sum(float(r.estimated_monthly_savings_usd or 0) for r in rows)
    probability = body.adoption_probability
    projected = gross * probability
    annual = projected * 12
    return {
        "organization_slug": body.organization_slug,
        "recommendation_count": len(rows),
        "adoption_probability": probability,
        "projected_monthly_savings_usd": round(projected, 2),
        "projected_annual_savings_usd": round(annual, 2),
        "selected": [
            {
                "recommendation_id": r.recommendation_id,
                "title": r.title,
                "estimated_monthly_savings_usd": float(r.estimated_monthly_savings_usd),
            }
            for r in rows
        ],
    }


@router.get("/investor/kpis")
async def investor_kpis(
    organization_slug: str = Query(..., description="Tenant slug"),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    metrics = await _metrics_from_actions(db, organization_slug)
    actions_res = await _finops_execute(
        db,
        select(FinOpsRecommendationAction).where(FinOpsRecommendationAction.organization_slug == organization_slug),
    )
    actions = list(actions_res.scalars().all())
    accepted = len([a for a in actions if a.status in {"accepted", "in_progress", "implemented", "verified"}])
    implemented = len([a for a in actions if a.status in {"implemented", "verified"}])
    verified = len([a for a in actions if a.status == "verified"])
    rolled_back = len([a for a in actions if a.rolled_back_at is not None])
    avg_conf = round(sum(float(a.confidence_score or 0) for a in actions) / max(len(actions), 1), 3)
    events_res = await _finops_execute(
        db,
        select(func.count(FinOpsActionEvent.id)).where(
            FinOpsActionEvent.organization_slug == organization_slug,
            FinOpsActionEvent.created_at >= (datetime.utcnow() - timedelta(days=30)),
        ),
    )
    monthly_events = int(events_res.scalar() or 0)
    return {
        "organization_slug": organization_slug,
        "kpis": {
            "activated_orgs": max(metrics["adoption"]["weekly_active_orgs"], 1),
            "time_to_first_saving_hours": metrics["activation"]["time_to_first_saving_hours"],
            "gross_savings_identified_usd": metrics["impact"]["recommended_savings_usd"],
            "net_realized_savings_usd": metrics["impact"]["realized_savings_30d_usd"],
            "recommendations_accepted": accepted,
            "recommendations_implemented": implemented,
            "recommendations_verified": verified,
            "recommendations_rolled_back": rolled_back,
            "average_confidence_score": avg_conf,
            "action_events_30d": monthly_events,
            "payback_period_months": round(
                max(metrics["impact"]["recommended_savings_usd"] - metrics["impact"]["realized_savings_30d_usd"], 0)
                / max(metrics["impact"]["realized_savings_30d_usd"], 1),
                2,
            ),
        },
    }


@router.get("/investor/report")
async def investor_report(
    organization_slug: str = Query(..., description="Tenant slug"),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    metrics = await _metrics_from_actions(db, organization_slug)
    kpi_payload = await investor_kpis(organization_slug=organization_slug, db=db)
    anomalies_payload = await list_anomalies(organization_slug=organization_slug, include_resolved=False, db=db)
    weekly = await weekly_digest(organization_slug=organization_slug, db=db)
    generated_at = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
    return {
        "meta": {"organization_slug": organization_slug, "generated_at": generated_at, "format": "investor_report_v1"},
        "kpis": kpi_payload["kpis"],
        "traction": {
            "activation": metrics["activation"],
            "impact": metrics["impact"],
            "adoption": metrics["adoption"],
        },
        "top_actions": metrics["top_actions"][:10],
        "weekly_digest": weekly,
        "open_anomalies": anomalies_payload["anomalies"],
    }


@router.get("/investor/report/export")
async def export_investor_report(
    organization_slug: str = Query(..., description="Tenant slug"),
    db: AsyncSession = Depends(get_db),
) -> Response:
    payload = await investor_report(organization_slug=organization_slug, db=db)
    body = json.dumps(jsonable_encoder(payload), indent=2)
    return Response(
        content=body,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="finops-investor-report-{organization_slug}.json"'
        },
    )
