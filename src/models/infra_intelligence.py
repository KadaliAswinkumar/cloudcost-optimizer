"""
Infrastructure Intelligence domain: organizations, connectors, scans, findings, reports, alerts.
Primary keys are UUID strings for SQLite (tests) and PostgreSQL compatibility.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


def _uuid_str() -> str:
    return str(uuid.uuid4())


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    connectors: Mapped[List["CloudConnector"]] = relationship(back_populates="organization")
    findings: Mapped[List["InfraFinding"]] = relationship(back_populates="organization")
    reports: Mapped[List["InfraReport"]] = relationship(back_populates="organization")
    alert_rules: Mapped[List["AlertRule"]] = relationship(back_populates="organization")


class CloudConnector(Base):
    """Customer cloud account connection (credentials encrypted at rest)."""

    __tablename__ = "cloud_connectors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    provider: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    credentials_ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_scan_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    organization: Mapped["Organization"] = relationship(back_populates="connectors")
    scan_jobs: Mapped[List["ScanJob"]] = relationship(back_populates="connector")


class ScanJob(Base):
    __tablename__ = "scan_jobs"
    __table_args__ = (Index("ix_scan_jobs_org_connector", "organization_id", "cloud_connector_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    cloud_connector_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cloud_connectors.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(
        String(24), default="pending", nullable=False, index=True
    )  # pending | running | completed | failed
    trigger: Mapped[str] = mapped_column(String(32), default="manual", nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    connector: Mapped["CloudConnector"] = relationship(back_populates="scan_jobs")
    snapshots: Mapped[List["AssetSnapshot"]] = relationship(back_populates="scan_job")
    findings: Mapped[List["InfraFinding"]] = relationship(back_populates="scan_job")


class AssetSnapshot(Base):
    """Versioned normalized asset graph (JSON) for one scan."""

    __tablename__ = "asset_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    scan_job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("scan_jobs.id", ondelete="CASCADE"), index=True
    )
    schema_version: Mapped[int] = mapped_column(default=1, nullable=False)
    graph_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    scan_job: Mapped["ScanJob"] = relationship(back_populates="snapshots")


class InfraFinding(Base):
    """Single rule outcome with evidence trail."""

    __tablename__ = "infra_findings"
    __table_args__ = (Index("ix_infra_findings_org_scan", "organization_id", "scan_job_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    cloud_connector_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cloud_connectors.id", ondelete="CASCADE"), index=True
    )
    scan_job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("scan_jobs.id", ondelete="CASCADE"), index=True
    )
    rule_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    rule_version: Mapped[str] = mapped_column(String(32), default="1.0.0", nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    remediation_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    estimated_monthly_savings: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(14, 2), nullable=True
    )
    resource_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(24), default="open", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    organization: Mapped["Organization"] = relationship(back_populates="findings")
    scan_job: Mapped["ScanJob"] = relationship(back_populates="findings")


class InfraReport(Base):
    __tablename__ = "infra_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    summary_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    organization: Mapped["Organization"] = relationship(back_populates="reports")


class AlertRule(Base):
    """Threshold / schedule definition; evaluation loop comes in Phase 2."""

    __tablename__ = "alert_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    condition_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    channel_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    last_evaluated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    organization: Mapped["Organization"] = relationship(back_populates="alert_rules")
