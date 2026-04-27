"""Run a scan job: collect graph, persist snapshot, evaluate rules, persist findings."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.infra_intelligence import (
    AssetSnapshot,
    CloudConnector,
    InfraFinding,
    ScanJob,
)
from src.services.infra_intelligence.collector_stub import build_stub_graph
from src.services.infra_intelligence.rule_engine import evaluate_graph

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


async def run_scan_job(session: AsyncSession, scan_job_id: str) -> ScanJob:
    """
    Execute scan synchronously within the request worker (MVP).

    Phase 2: enqueue Celery / separate worker for long-running collectors.
    """
    result = await session.execute(select(ScanJob).where(ScanJob.id == scan_job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise ValueError("scan_job not found")

    conn_result = await session.execute(
        select(CloudConnector).where(CloudConnector.id == job.cloud_connector_id)
    )
    connector = conn_result.scalar_one_or_none()
    if not connector:
        job.status = "failed"
        job.error_message = "connector not found"
        job.completed_at = datetime.utcnow()
        await session.flush()
        return job

    job.status = "running"
    job.started_at = datetime.utcnow()
    job.error_message = None
    await session.flush()

    try:
        # Real collectors would decrypt credentials and call cloud APIs here.
        _ = connector.credentials_ciphertext  # noqa: F841 — touch field for future use
        graph = build_stub_graph(connector.provider)

        snapshot = AssetSnapshot(
            scan_job_id=job.id,
            schema_version=int(graph.get("schema_version", 1)),
            graph_json=graph,
        )
        session.add(snapshot)
        await session.flush()

        raw_findings = evaluate_graph(graph, connector.id)
        for f in raw_findings:
            session.add(
                InfraFinding(
                    organization_id=job.organization_id,
                    cloud_connector_id=connector.id,
                    scan_job_id=job.id,
                    rule_id=f["rule_id"],
                    rule_version=f["rule_version"],
                    category=f["category"],
                    severity=f["severity"],
                    title=f["title"],
                    description=f["description"],
                    evidence_json=f["evidence_json"],
                    remediation_json=f.get("remediation_json"),
                    estimated_monthly_savings=f.get("estimated_monthly_savings"),
                    resource_key=f.get("resource_key"),
                    status="open",
                )
            )

        job.status = "completed"
        job.completed_at = datetime.utcnow()
        connector.last_scan_at = job.completed_at
        connector.last_error = None
        await session.flush()
        logger.info(
            "scan_job completed",
            extra={
                "scan_job_id": job.id,
                "findings": len(raw_findings),
                "connector_id": connector.id,
            },
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("scan_job failed")
        job.status = "failed"
        job.completed_at = datetime.utcnow()
        job.error_message = str(exc)[:8000]
        connector.last_error = job.error_message
        await session.flush()

    return job
