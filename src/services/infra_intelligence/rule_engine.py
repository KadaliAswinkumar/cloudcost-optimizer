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
    cost_summary = graph.get("cost_summary") if isinstance(graph.get("cost_summary"), dict) else {}

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

        if rtype == "ec2_instance":
            itype = str(attrs.get("instance_type") or "")
            cpu_avg = float(attrs.get("cpu_avg_14d_pct") or 0)
            cpu_max = float(attrs.get("cpu_max_14d_pct") or 0)
            if attrs.get("state") == "running" and cpu_avg > 0 and cpu_avg < 15:
                findings.append(
                    {
                        "rule_id": "cost.ec2.low_cpu_utilization_rightsize",
                        "rule_version": "1.0.0",
                        "category": "cost",
                        "severity": "high",
                        "title": "Running EC2 instance shows low CPU utilization",
                        "description": (
                            f"Instance {res.get('id')} averages {cpu_avg:.1f}% CPU over 14 days "
                            f"(max {cpu_max:.1f}%). Potential rightsizing candidate."
                        ),
                        "evidence_json": {"connector_id": connector_id, "resource": res},
                        "remediation_json": {
                            "steps": [
                                "Evaluate a smaller instance family or Graviton equivalent.",
                                "Validate memory/network utilization before rightsizing.",
                                "Use scheduled scaling for predictable off-hours demand.",
                            ]
                        },
                        "estimated_monthly_savings": Decimal("110.00"),
                        "resource_key": f"{provider}:{res.get('id')}:low-cpu",
                    }
                )
            if itype.startswith(("m4.", "c4.", "r4.", "t2.")):
                findings.append(
                    {
                        "rule_id": "cost.ec2.old_generation_instance_family",
                        "rule_version": "1.0.0",
                        "category": "cost",
                        "severity": "medium",
                        "title": "Older EC2 generation detected",
                        "description": (
                            f"Instance {res.get('id')} runs {itype}. "
                            "Newer generations often provide better price/performance."
                        ),
                        "evidence_json": {"connector_id": connector_id, "resource": res},
                        "remediation_json": {
                            "steps": [
                                "Benchmark equivalent workload on current generation families (m6i/m7g/c7g/r7g).",
                                "Prefer Graviton when architecture compatibility allows.",
                            ]
                        },
                        "estimated_monthly_savings": Decimal("80.00"),
                        "resource_key": f"{provider}:{res.get('id')}:oldgen",
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

        if rtype == "eks_nodegroup":
            desired = int(attrs.get("desired_size") or 0)
            minimum = int(attrs.get("min_size") or 0)
            maximum = int(attrs.get("max_size") or 0)
            cap_type = str(attrs.get("capacity_type") or "ON_DEMAND")
            if desired > max(minimum, 0) + 2:
                findings.append(
                    {
                        "rule_id": "cost.eks.nodegroup_overprovisioned",
                        "rule_version": "1.0.0",
                        "category": "cost",
                        "severity": "high",
                        "title": "EKS nodegroup appears over-provisioned",
                        "description": (
                            f"Nodegroup {res.get('id')} desired={desired}, min={minimum}, max={maximum}. "
                            "Consider rightsizing node counts and using Karpenter/Cluster Autoscaler."
                        ),
                        "evidence_json": {"connector_id": connector_id, "resource": res},
                        "remediation_json": {
                            "steps": [
                                "Review pod requests/limits and idle headroom.",
                                "Reduce desired size or enable dynamic scaling.",
                                "Shift suitable workloads to Spot nodegroups for 50-70% lower compute cost.",
                            ]
                        },
                        "estimated_monthly_savings": Decimal(str(max(120, (desired - minimum) * 65))),
                        "resource_key": f"{provider}:{res.get('id')}:eks-overprov",
                    }
                )
            if cap_type.upper() == "ON_DEMAND":
                findings.append(
                    {
                        "rule_id": "cost.eks.nodegroup_spot_mix_missing",
                        "rule_version": "1.0.0",
                        "category": "cost",
                        "severity": "medium",
                        "title": "EKS nodegroup is fully On-Demand",
                        "description": (
                            f"Nodegroup {res.get('id')} uses On-Demand capacity only. "
                            "Non-critical workloads can benefit from Spot mixes."
                        ),
                        "evidence_json": {"connector_id": connector_id, "resource": res},
                        "remediation_json": {
                            "steps": [
                                "Create a separate Spot nodegroup for fault-tolerant workloads.",
                                "Use PodDisruptionBudgets and priority classes for safer eviction handling.",
                            ]
                        },
                        "estimated_monthly_savings": Decimal("180.00"),
                        "resource_key": f"{provider}:{res.get('id')}:eks-spot",
                    }
                )

        if rtype == "rds_instance":
            multi_az = bool(attrs.get("multi_az", False))
            if not multi_az:
                findings.append(
                    {
                        "rule_id": "architecture.rds.single_az",
                        "rule_version": "1.0.0",
                        "category": "architecture",
                        "severity": "low",
                        "title": "RDS instance is single-AZ",
                        "description": (
                            f"Database {res.get('id')} is not Multi-AZ. This can increase resilience risk."
                        ),
                        "evidence_json": {"connector_id": connector_id, "resource": res},
                        "remediation_json": {
                            "steps": [
                                "Enable Multi-AZ for production databases requiring high availability.",
                                "For non-production, keep single-AZ but enforce backup/restore drills.",
                            ]
                        },
                        "estimated_monthly_savings": None,
                        "resource_key": f"{provider}:{res.get('id')}:rds-single-az",
                    }
                )
            if str(attrs.get("storage_type") or "").lower() == "gp2":
                findings.append(
                    {
                        "rule_id": "cost.rds.gp2_to_gp3",
                        "rule_version": "1.0.0",
                        "category": "cost",
                        "severity": "medium",
                        "title": "RDS storage type gp2 can often be optimized to gp3",
                        "description": (
                            f"Database {res.get('id')} uses gp2 storage. "
                            "Migrating to gp3 can reduce storage costs in many workloads."
                        ),
                        "evidence_json": {"connector_id": connector_id, "resource": res},
                        "remediation_json": {
                            "steps": [
                                "Evaluate current IOPS/throughput utilization before migration.",
                                "Migrate to gp3 and tune provisioned performance as needed.",
                            ]
                        },
                        "estimated_monthly_savings": Decimal("70.00"),
                        "resource_key": f"{provider}:{res.get('id')}:rds-gp3",
                    }
                )

        if rtype == "ecs_service":
            desired = int(attrs.get("desired_count") or 0)
            running = int(attrs.get("running_count") or 0)
            launch_type = str(attrs.get("launch_type") or "UNKNOWN").upper()
            cpu_avg = float(attrs.get("cpu_avg_14d_pct") or 0)
            mem_avg = float(attrs.get("memory_avg_14d_pct") or 0)
            if desired >= 4 and running >= 4:
                findings.append(
                    {
                        "rule_id": "cost.ecs.service_high_desired_count",
                        "rule_version": "1.0.0",
                        "category": "cost",
                        "severity": "medium",
                        "title": "ECS service has high steady task count",
                        "description": (
                            f"ECS service {res.get('id')} runs desired/running {desired}/{running}. "
                            "Review autoscaling and off-hours scaling policies."
                        ),
                        "evidence_json": {"connector_id": connector_id, "resource": res},
                        "remediation_json": {
                            "steps": [
                                "Enable target tracking autoscaling based on CPU/memory/queue depth.",
                                "For non-prod, reduce minimum task counts outside business hours.",
                            ]
                        },
                        "estimated_monthly_savings": Decimal(str(max(80, desired * 25))),
                        "resource_key": f"{provider}:{res.get('id')}:ecs-taskcount",
                    }
                )
            if cpu_avg > 0 and cpu_avg < 20 and mem_avg > 0 and mem_avg < 25 and desired >= 2:
                findings.append(
                    {
                        "rule_id": "cost.ecs.low_utilization_rightsize",
                        "rule_version": "1.0.0",
                        "category": "cost",
                        "severity": "high",
                        "title": "ECS service appears underutilized",
                        "description": (
                            f"ECS service {res.get('id')} has low utilization "
                            f"(CPU {cpu_avg:.1f}%, Memory {mem_avg:.1f}%)."
                        ),
                        "evidence_json": {"connector_id": connector_id, "resource": res},
                        "remediation_json": {
                            "steps": [
                                "Reduce minimum/desired task counts based on real demand.",
                                "Tune CPU/memory reservations and autoscaling targets.",
                            ]
                        },
                        "estimated_monthly_savings": Decimal(str(max(90, desired * 30))),
                        "resource_key": f"{provider}:{res.get('id')}:ecs-lowutil",
                    }
                )
            if launch_type == "EC2":
                findings.append(
                    {
                        "rule_id": "cost.ecs.launch_type_ec2_only",
                        "rule_version": "1.0.0",
                        "category": "cost",
                        "severity": "low",
                        "title": "ECS service runs on EC2 launch type only",
                        "description": (
                            f"ECS service {res.get('id')} uses EC2 launch type. "
                            "Mixed Fargate/Fargate Spot may reduce ops overhead and cost for suitable workloads."
                        ),
                        "evidence_json": {"connector_id": connector_id, "resource": res},
                        "remediation_json": {
                            "steps": [
                                "Assess migration of stateless services to Fargate/Fargate Spot.",
                                "Use capacity provider strategy for blended resilience/cost.",
                            ]
                        },
                        "estimated_monthly_savings": Decimal("55.00"),
                        "resource_key": f"{provider}:{res.get('id')}:ecs-launchtype",
                    }
                )

        if rtype == "lambda_function":
            memory_mb = int(attrs.get("memory_mb") or 0)
            invocations = float(attrs.get("invocations_14d") or 0)
            if memory_mb >= 1024:
                findings.append(
                    {
                        "rule_id": "cost.lambda.high_memory_config",
                        "rule_version": "1.0.0",
                        "category": "cost",
                        "severity": "low",
                        "title": "Lambda configured with high memory allocation",
                        "description": (
                            f"Lambda {res.get('id')} is configured with {memory_mb} MB memory. "
                            "Tune memory with power tuning benchmarks to avoid overprovisioning."
                        ),
                        "evidence_json": {"connector_id": connector_id, "resource": res},
                        "remediation_json": {
                            "steps": [
                                "Run AWS Lambda Power Tuning on representative payloads.",
                                "Reduce memory where latency impact is acceptable.",
                            ]
                        },
                        "estimated_monthly_savings": Decimal("30.00"),
                        "resource_key": f"{provider}:{res.get('id')}:lambda-memory",
                    }
                )
            if memory_mb >= 1024 and invocations < 150:
                findings.append(
                    {
                        "rule_id": "cost.lambda.low_traffic_overprovisioned",
                        "rule_version": "1.0.0",
                        "category": "cost",
                        "severity": "medium",
                        "title": "Lambda is low-traffic but high-memory",
                        "description": (
                            f"Lambda {res.get('id')} has only {invocations:.0f} invocations over 14 days "
                            f"with {memory_mb} MB configured."
                        ),
                        "evidence_json": {"connector_id": connector_id, "resource": res},
                        "remediation_json": {
                            "steps": [
                                "Rightsize memory and use provisioned concurrency only when needed.",
                                "Consolidate rarely used functions where possible.",
                            ]
                        },
                        "estimated_monthly_savings": Decimal("20.00"),
                        "resource_key": f"{provider}:{res.get('id')}:lambda-lowtraffic",
                    }
                )

        if rtype == "s3_bucket":
            rules = int(attrs.get("lifecycle_rules") or 0)
            if rules == 0:
                findings.append(
                    {
                        "rule_id": "cost.s3.no_lifecycle_rules",
                        "rule_version": "1.0.0",
                        "category": "cost",
                        "severity": "low",
                        "title": "S3 bucket has no lifecycle policy",
                        "description": (
                            f"Bucket {res.get('id')} has no lifecycle rules. "
                            "Storage tiering/expiry often reduces long-tail costs."
                        ),
                        "evidence_json": {"connector_id": connector_id, "resource": res},
                        "remediation_json": {
                            "steps": [
                                "Define lifecycle transitions for infrequent/archival data.",
                                "Expire incomplete multipart uploads and stale objects.",
                            ]
                        },
                        "estimated_monthly_savings": Decimal("25.00"),
                        "resource_key": f"{provider}:{res.get('id')}:s3-lifecycle",
                    }
                )

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

    if cost_summary.get("status") == "ok":
        total_cost = Decimal(str(cost_summary.get("total_unblended_cost_usd") or 0))
        cc = cost_summary.get("commitment_coverage") or {}
        ri_cov = Decimal(str(cc.get("ec2_reservation_coverage_pct") or 0))
        sp_cov = Decimal(str(cc.get("ec2_savings_plan_coverage_pct") or 0))
        combined_cov = ri_cov + sp_cov
        if combined_cov < Decimal("45"):
            findings.append(
                {
                    "rule_id": "cost.commitment.ec2_coverage_low",
                    "rule_version": "1.0.0",
                    "category": "cost",
                    "severity": "high",
                    "title": "EC2 commitment coverage appears low",
                    "description": (
                        f"Estimated EC2 commitment coverage (RI + Savings Plans) is about {combined_cov:.1f}%. "
                        "Steady workloads may be overpaying On-Demand rates."
                    ),
                    "evidence_json": {"connector_id": connector_id, "commitment_coverage": cc},
                    "remediation_json": {
                        "steps": [
                            "Quantify baseline EC2 demand and evaluate 1-year Savings Plans first.",
                            "Layer RIs for highly predictable always-on instances.",
                        ]
                    },
                    "estimated_monthly_savings": Decimal("250.00"),
                    "resource_key": f"{provider}:commitment:ec2",
                }
            )
        if total_cost > Decimal("0"):
            for entry in list(cost_summary.get("by_service") or [])[:5]:
                service_name = str(entry.get("service") or "Unknown Service")
                service_cost = Decimal(str(entry.get("unblended_cost_usd") or 0))
                if service_cost < Decimal("200"):
                    continue
                share = (service_cost / total_cost) * Decimal("100")
                if share < Decimal("15"):
                    continue
                target_pct = Decimal("0.25")
                if "Elastic Compute Cloud" in service_name:
                    target_pct = Decimal("0.35")
                    if combined_cov < Decimal("45"):
                        target_pct = Decimal("0.42")
                elif "Kubernetes Service" in service_name:
                    target_pct = Decimal("0.40")
                elif "Relational Database Service" in service_name:
                    target_pct = Decimal("0.22")
                est = (service_cost * target_pct).quantize(Decimal("0.01"))
                findings.append(
                    {
                        "rule_id": f"cost.service.top_spend.{service_name.lower().replace(' ', '_')[:40]}",
                        "rule_version": "1.0.0",
                        "category": "cost",
                        "severity": "high" if share >= Decimal("25") else "medium",
                        "title": f"High spend concentration detected: {service_name}",
                        "description": (
                            f"{service_name} represents approximately {share:.1f}% of 30-day spend. "
                            "Targeted optimization in this service can unlock material savings."
                        ),
                        "evidence_json": {
                            "connector_id": connector_id,
                            "service_name": service_name,
                            "service_cost_30d_usd": float(service_cost),
                            "total_cost_30d_usd": float(total_cost),
                            "share_percent": float(share),
                            "cost_summary": cost_summary,
                        },
                        "remediation_json": {
                            "steps": [
                                "Prioritize rightsizing and commitment strategy for top-spend services.",
                                "Adopt Spot/Graviton/container autoscaling where suitable.",
                                "Track realized savings against this service baseline weekly.",
                            ]
                        },
                        "estimated_monthly_savings": est,
                        "resource_key": f"{provider}:cost:{service_name.lower()[:80]}",
                    }
                )

    return findings
