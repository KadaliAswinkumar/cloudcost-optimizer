"""
Deterministic rule engine over normalized asset graph (v1).

Each rule returns a dict compatible with InfraFinding columns.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List


def evaluate_graph(graph: Dict[str, Any], connector_id: str) -> List[Dict[str, Any]]:
    """Run all built-in rules; connector_id is embedded in evidence for traceability."""
    findings: List[Dict[str, Any]] = []
    resources = graph.get("resources") or []

    for res in resources:
        rtype = res.get("type")
        attrs = res.get("attributes") or {}

        if rtype == "ec2_instance" and attrs.get("state") == "stopped":
            itype = attrs.get("instance_type", "unknown")
            findings.append(
                {
                    "rule_id": "cost.stopped_instance.monthly_charge",
                    "rule_version": "1.0.0",
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
                    "resource_key": f"{graph.get('provider')}:{res.get('id')}",
                }
            )

        if rtype == "security_group":
            for rule in attrs.get("ingress") or []:
                if rule.get("cidr") != "0.0.0.0/0":
                    continue
                fp = rule.get("from_port")
                tp = rule.get("to_port")
                if fp is None or tp is None:
                    continue
                if int(fp) <= 22 <= int(tp):
                    findings.append(
                        {
                            "rule_id": "security.sg.ssh_open_to_world",
                            "rule_version": "1.0.0",
                            "category": "security",
                            "severity": "high",
                            "title": "Security group allows SSH from the entire internet",
                            "description": (
                                f"Security group {res.get('id')} permits SSH (22) from 0.0.0.0/0."
                            ),
                            "evidence_json": {
                                "connector_id": connector_id,
                                "resource": res,
                                "matched_ingress": rule,
                            },
                            "remediation_json": {
                                "steps": [
                                    "Restrict SSH to bastion IPs or VPN CIDRs.",
                                    "Prefer SSM Session Manager instead of SSH where possible.",
                                ]
                            },
                            "estimated_monthly_savings": None,
                            "resource_key": f"{graph.get('provider')}:{res.get('id')}:ssh",
                        }
                    )

    nat_count = sum(1 for r in resources if r.get("type") == "nat_gateway")
    if nat_count == 1:
        findings.append(
            {
                "rule_id": "architecture.single_nat_gateway",
                "rule_version": "1.0.0",
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
                "resource_key": f"{graph.get('provider')}:nat:single",
            }
        )

    return findings
