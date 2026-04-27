"""
Deterministic rule engine over normalized asset graph (v1).

Output rows match InfraFinding columns (except ORM ids).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple


def _port_range(
    from_port: Any, to_port: Any, protocol: str
) -> Tuple[int, int]:
    """Map AWS-style nullable ports to inclusive numeric range."""
    if str(protocol) == "-1" or (from_port is None and to_port is None):
        return 0, 65535
    fp = int(from_port) if from_port is not None else 0
    tp = int(to_port) if to_port is not None else 65535
    return fp, tp


def _port_in_range(port: int, lo: int, hi: int) -> bool:
    return lo <= port <= hi


def _finding_ingress_world_port(
    *,
    graph: Dict[str, Any],
    connector_id: str,
    res: Dict[str, Any],
    ingress_row: Dict[str, Any],
    port: int,
    label: str,
    rule_id: str,
    severity: str,
) -> Optional[Dict[str, Any]]:
    lo, hi = _port_range(
        ingress_row.get("from_port"),
        ingress_row.get("to_port"),
        str(ingress_row.get("protocol", "tcp")),
    )
    if not _port_in_range(port, lo, hi):
        return None
    cidr = ingress_row.get("cidr") or ""
    if cidr not in ("0.0.0.0/0", "::/0"):
        return None
    return {
        "rule_id": rule_id,
        "rule_version": "1.1.0",
        "category": "security",
        "severity": severity,
        "title": f"Security group allows {label} from the entire internet",
        "description": (
            f"Security group {res.get('id')} permits {label} (port {port}) from {cidr}."
        ),
        "evidence_json": {
            "connector_id": connector_id,
            "resource": res,
            "matched_ingress": ingress_row,
        },
        "remediation_json": {
            "steps": [
                f"Restrict {label} to bastion IPs, VPN CIDRs, or use a managed access path.",
                "Prefer SSM Session Manager instead of open SSH where possible.",
            ]
        },
        "estimated_monthly_savings": None,
        "resource_key": f"{graph.get('provider')}:{res.get('id')}:{label}",
    }


def evaluate_graph(graph: Dict[str, Any], connector_id: str) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    resources: List[Dict[str, Any]] = list(graph.get("resources") or [])
    provider = graph.get("provider") or "unknown"

    for res in resources:
        rtype = res.get("type")
        attrs = res.get("attributes") or {}

        if rtype == "ec2_instance" and attrs.get("state") == "stopped":
            itype = attrs.get("instance_type", "unknown")
            findings.append(
                {
                    "rule_id": "cost.stopped_instance.monthly_charge",
                    "rule_version": "1.1.0",
                    "category": "cost",
                    "severity": "medium",
                    "title": "Stopped EC2 may still incur EBS and elastic IP costs",
                    "description": (
                        f"Instance {res.get('id')} ({itype}) is stopped. "
                        "Verify attached volumes and IPs are still required."
                    ),
                    "evidence_json": {
                        "connector_id": connector_id,
                        "resource": res,
                        "graph_schema_version": graph.get("schema_version"),
                    },
                    "remediation_json": {
                        "steps": [
                            "Review attached EBS volumes and snapshots.",
                            "Release unassociated Elastic IPs.",
                            "Terminate if the instance is permanently unused.",
                        ]
                    },
                    "estimated_monthly_savings": Decimal("45.00"),
                    "resource_key": f"{provider}:{res.get('id')}",
                }
            )

        if rtype == "ebs_volume":
            if attrs.get("state") == "available" and int(attrs.get("attachment_count") or 0) == 0:
                size = int(attrs.get("size_gb") or 0)
                est = Decimal(str(max(1, size) * 0.1))
                findings.append(
                    {
                        "rule_id": "cost.unattached_ebs_volume",
                        "rule_version": "1.1.0",
                        "category": "cost",
                        "severity": "medium",
                        "title": "Unattached EBS volume is accruing storage cost",
                        "description": (
                            f"Volume {res.get('id')} is available with no attachments ({size} GiB)."
                        ),
                        "evidence_json": {"connector_id": connector_id, "resource": res},
                        "remediation_json": {
                            "steps": [
                                "Snapshot if retention is required, then delete the volume.",
                                "Attach to an instance if still needed.",
                            ]
                        },
                        "estimated_monthly_savings": est,
                        "resource_key": f"{provider}:{res.get('id')}",
                    }
                )

        if rtype == "security_group":
            for row in attrs.get("ingress") or []:
                cidr = row.get("cidr") or ""
                proto = str(row.get("protocol", "tcp"))
                if cidr == "0.0.0.0/0" and proto == "-1":
                    findings.append(
                        {
                            "rule_id": "security.sg.all_traffic_open_to_world",
                            "rule_version": "1.1.0",
                            "category": "security",
                            "severity": "critical",
                            "title": "Security group allows all traffic from the internet (IPv4)",
                            "description": (
                                f"Security group {res.get('id')} has unrestricted ingress from 0.0.0.0/0."
                            ),
                            "evidence_json": {
                                "connector_id": connector_id,
                                "resource": res,
                                "matched_ingress": row,
                            },
                            "remediation_json": {
                                "steps": [
                                    "Remove 0.0.0.0/0 ingress or replace with specific CIDRs.",
                                    "Split security groups by least privilege.",
                                ]
                            },
                            "estimated_monthly_savings": None,
                            "resource_key": f"{provider}:{res.get('id')}:alltraffic",
                        }
                    )
                    continue

                for port, label, rid, sev in (
                    (22, "SSH", "security.sg.ssh_open_to_world", "high"),
                    (3389, "RDP", "security.sg.rdp_open_to_world", "high"),
                ):
                    f = _finding_ingress_world_port(
                        graph=graph,
                        connector_id=connector_id,
                        res=res,
                        ingress_row=row,
                        port=port,
                        label=label,
                        rule_id=rid,
                        severity=sev,
                    )
                    if f:
                        findings.append(f)

    nat_count = sum(1 for r in resources if r.get("type") == "nat_gateway")
    if nat_count == 1:
        findings.append(
            {
                "rule_id": "architecture.single_nat_gateway",
                "rule_version": "1.1.0",
                "category": "architecture",
                "severity": "low",
                "title": "Single NAT gateway may be a resilience bottleneck",
                "description": (
                    "Only one NAT gateway was discovered in the snapshot. "
                    "Multi-AZ workloads often need redundancy or egress alternatives."
                ),
                "evidence_json": {
                    "connector_id": connector_id,
                    "nat_count": nat_count,
                    "resources": [r for r in resources if r.get("type") == "nat_gateway"],
                },
                "remediation_json": {
                    "steps": [
                        "Evaluate per-AZ NAT or NAT-less patterns where acceptable.",
                        "Document RTO/RPO for AZ loss impacting egress.",
                    ]
                },
                "estimated_monthly_savings": Decimal("120.00"),
                "resource_key": f"{provider}:nat:single",
            }
        )

    return findings
