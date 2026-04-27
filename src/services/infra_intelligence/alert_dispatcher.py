"""Dispatch alert channels when new findings match org rules (webhook MVP)."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.infra_intelligence import AlertRule, InfraFinding

logger = logging.getLogger(__name__)

_SEVERITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}


def _severity_meets_min(finding_severity: str, min_severity: str) -> bool:
    fs = _SEVERITY_ORDER.get(finding_severity.lower(), 0)
    ms = _SEVERITY_ORDER.get((min_severity or "info").lower(), 0)
    return fs >= ms


async def dispatch_webhooks_for_new_findings(
    session: AsyncSession,
    organization_id: str,
    findings: List[InfraFinding],
) -> None:
    if not findings:
        return
    res = await session.execute(
        select(AlertRule).where(
            AlertRule.organization_id == organization_id,
            AlertRule.enabled.is_(True),
        )
    )
    rules = list(res.scalars().all())
    if not rules:
        return

    async with httpx.AsyncClient(timeout=10.0) as client:
        for rule in rules:
            cond = rule.condition_json or {}
            min_sev = cond.get("min_severity", "high")
            matched = [f for f in findings if _severity_meets_min(f.severity, min_sev)]
            if not matched:
                continue
            ch = rule.channel_json or {}
            if ch.get("type") != "webhook" or not ch.get("url"):
                continue
            payload: Dict[str, Any] = {
                "alert_rule_id": rule.id,
                "alert_rule_name": rule.name,
                "organization_id": organization_id,
                "finding_count": len(matched),
                "findings": [
                    {
                        "id": f.id,
                        "severity": f.severity,
                        "category": f.category,
                        "title": f.title,
                        "rule_id": f.rule_id,
                    }
                    for f in matched
                ],
            }
            try:
                r = await client.post(str(ch["url"]), json=payload)
                r.raise_for_status()
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "webhook delivery failed",
                    extra={"rule_id": rule.id, "error": str(exc)},
                )
