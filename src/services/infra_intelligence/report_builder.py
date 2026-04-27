"""Roll up findings into report summary JSON."""

from __future__ import annotations

from collections import Counter
from decimal import Decimal
from typing import Any, Dict, List


def build_report_summary(
    *,
    title: str,
    scan_job_ids: List[str],
    findings_payload: List[Dict[str, Any]],
) -> Dict[str, Any]:
    by_severity = Counter(f.get("severity") for f in findings_payload)
    by_category = Counter(f.get("category") for f in findings_payload)
    savings = [f.get("estimated_monthly_savings") for f in findings_payload if f.get("estimated_monthly_savings")]
    total_savings = sum((Decimal(str(x)) for x in savings), Decimal("0"))

    return {
        "title": title,
        "scan_job_ids": scan_job_ids,
        "finding_count": len(findings_payload),
        "by_severity": dict(by_severity),
        "by_category": dict(by_category),
        "estimated_monthly_savings_total": str(total_savings),
        "top_findings": findings_payload[:10],
    }
