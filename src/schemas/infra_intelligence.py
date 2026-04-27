"""Pydantic schemas for Infrastructure Intelligence API."""

from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=2, max_length=80, pattern=r"^[a-z0-9][a-z0-9-]*$")

    @field_validator("slug", mode="before")
    @classmethod
    def normalize_slug(cls, v: object) -> str:
        """Lowercase, allow spaces/underscores from UI, enforce leading alphanumeric."""
        if v is None:
            return ""
        s = str(v).strip().lower()
        s = re.sub(r"[^a-z0-9-]+", "-", s)
        s = re.sub(r"-{2,}", "-", s).strip("-")
        if not s:
            raise ValueError("slug cannot be empty")
        if not re.match(r"^[a-z0-9]", s):
            raise ValueError("slug must start with a letter or digit (e.g. my-company)")
        return s[:80]


class OrganizationOut(BaseModel):
    id: str
    name: str
    slug: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ConnectorCreate(BaseModel):
    provider: str = Field(..., description="aws | gcp | azure")
    display_name: str = Field(..., min_length=1, max_length=200)
    credentials: Dict[str, Any] = Field(
        default_factory=dict,
        description="Provider-specific secret fields; stored encrypted (never returned).",
    )

    @field_validator("provider")
    @classmethod
    def provider_ok(cls, v: str) -> str:
        allowed = {"aws", "gcp", "azure"}
        if v.lower() not in allowed:
            raise ValueError(f"provider must be one of {allowed}")
        return v.lower()


class ConnectorOut(BaseModel):
    id: str
    organization_id: str
    provider: str
    display_name: str
    status: str
    last_error: Optional[str] = None
    last_scan_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ScanCreate(BaseModel):
    trigger: str = Field(default="manual", max_length=32)


class ScanJobOut(BaseModel):
    id: str
    organization_id: str
    cloud_connector_id: str
    status: str
    trigger: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AssetSnapshotOut(BaseModel):
    id: str
    scan_job_id: str
    schema_version: int
    created_at: datetime

    model_config = {"from_attributes": True}


class FindingOut(BaseModel):
    id: str
    organization_id: str
    cloud_connector_id: str
    scan_job_id: str
    rule_id: str
    rule_version: str
    category: str
    severity: str
    title: str
    description: str
    evidence_json: Dict[str, Any]
    remediation_json: Optional[Dict[str, Any]] = None
    estimated_monthly_savings: Optional[Decimal] = None
    resource_key: Optional[str] = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    scan_job_ids: List[str] = Field(default_factory=list, description="Findings from these scans")


class ReportOut(BaseModel):
    id: str
    organization_id: str
    title: str
    summary_json: Dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertRuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    enabled: bool = True
    condition_json: Dict[str, Any] = Field(default_factory=dict)
    channel_json: Dict[str, Any] = Field(default_factory=dict)


class AlertRuleOut(BaseModel):
    id: str
    organization_id: str
    name: str
    enabled: bool
    condition_json: Dict[str, Any]
    channel_json: Dict[str, Any]
    last_evaluated_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}
