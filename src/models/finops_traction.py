"""
FinOps traction models for recommendation lifecycle, onboarding, and growth metrics.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from sqlalchemy import DateTime, Index, Numeric, String, Text
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


def _uuid_str() -> str:
    return str(uuid.uuid4())


class FinOpsRecommendationAction(Base):
    """
    Tracks recommendation lifecycle states for investor-grade impact proof.
    """

    __tablename__ = "finops_recommendation_actions"
    __table_args__ = (
        Index("ix_finops_action_org_status", "organization_slug", "status"),
        Index("ix_finops_action_rec_org", "recommendation_id", "organization_slug"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    organization_slug: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    recommendation_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    cloud_provider: Mapped[str] = mapped_column(String(16), nullable=False, default="aws")
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="open")
    confidence_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0.75)
    confidence_level: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    confidence_reasons_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    effort_level: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    risk_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0.5)
    blast_radius: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    decision_bucket: Mapped[str] = mapped_column(String(24), nullable=False, default="review_manually")
    estimated_monthly_savings_usd: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    realized_monthly_savings_usd: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    context_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    actioned_by: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    in_progress_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    implemented_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    dismissed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    rolled_back_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    rollback_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verification_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FinOpsIngestionSource(Base):
    """
    Onboarding and ingestion health across CSV/FOCUS and cloud exports.
    """

    __tablename__ = "finops_ingestion_sources"
    __table_args__ = (
        Index("ix_finops_source_org_type", "organization_slug", "source_type"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    organization_slug: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")
    freshness_status: Mapped[str] = mapped_column(String(24), nullable=False, default="unknown")
    records_ingested: Mapped[int] = mapped_column(default=0, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0.65)
    details_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FinOpsActionEvent(Base):
    """Event log for lifecycle transitions and investor proof trail."""

    __tablename__ = "finops_action_events"
    __table_args__ = (
        Index("ix_finops_event_org_time", "organization_slug", "created_at"),
        Index("ix_finops_event_rec", "recommendation_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    organization_slug: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    recommendation_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(24), nullable=False)
    actor: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    payload_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class FinOpsAnomalyEvent(Base):
    """Spend anomaly and regression signal tracking."""

    __tablename__ = "finops_anomaly_events"
    __table_args__ = (
        Index("ix_finops_anomaly_org_status", "organization_slug", "status"),
        Index("ix_finops_anomaly_time", "detected_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    organization_slug: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    anomaly_type: Mapped[str] = mapped_column(String(40), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="open")
    metric_name: Mapped[str] = mapped_column(String(80), nullable=False)
    baseline_value: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    observed_value: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    deviation_pct: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False, default=0)
    details_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
