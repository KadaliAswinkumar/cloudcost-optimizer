"""Run scan jobs outside the HTTP request transaction (own DB session + commit)."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from sqlalchemy import select

from src.core.database import async_session_factory
from src.models.infra_intelligence import ScanJob
from src.services.infra_intelligence.scan_service import run_scan_job

logger = logging.getLogger(__name__)


def schedule_scan_job(scan_job_id: str) -> None:
    """Fire-and-forget async scan on the running event loop (production default)."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        logger.error("schedule_scan_job called without running event loop")
        return
    loop.create_task(execute_scan_job_background(scan_job_id))


async def execute_scan_job_background(scan_job_id: str) -> None:
    async with async_session_factory() as session:
        try:
            await run_scan_job(session, scan_job_id)
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("scan background task crashed", extra={"scan_job_id": scan_job_id})
            async with async_session_factory() as session2:
                res = await session2.execute(select(ScanJob).where(ScanJob.id == scan_job_id))
                job = res.scalar_one_or_none()
                if job and job.status in ("pending", "running"):
                    job.status = "failed"
                    job.completed_at = datetime.utcnow()
                    job.error_message = "Internal error during background scan"
                    await session2.commit()
