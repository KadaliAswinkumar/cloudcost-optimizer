"""Run a scan job: decrypt creds, collect graph, snapshot, rules, findings, optional webhooks."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.field_encryption import decrypt_string
from src.models.infra_intelligence import (
    AssetSnapshot,
    CloudConnector,
    InfraFinding,
    ScanJob,
)
from src.services.infra_intelligence.alert_dispatcher import dispatch_webhooks_for_new_findings
from src.services.infra_intelligence.collector import collect_asset_graph
from src.services.infra_intelligence.rule_engine import evaluate_graph

logger = logging.getLogger(__name__)


def _load_connector_credentials(ciphertext: str) -> Dict[str, Any]:
    try:
        raw = decrypt_string(ciphertext)
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except (ValueError, json.JSONDecodeError):
        return {}


async def run_scan_job(session: AsyncSession, scan_job_id: str) -> ScanJob:
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
        creds = _load_connector_credentials(connector.credentials_ciphertext)
        graph = await collect_asset_graph(connector.provider, creds)

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

        await session.flush()
        fin_res = await session.execute(
            select(InfraFinding).where(InfraFinding.scan_job_id == job.id)
        )
        persisted = list(fin_res.scalars().all())
        try:
            await dispatch_webhooks_for_new_findings(session, job.organization_id, persisted)
        except Exception:
            logger.warning("alert dispatch skipped due to error", exc_info=True)

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
                "mode": graph.get("collection_mode"),
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
