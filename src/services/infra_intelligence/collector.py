"""
Asset graph collection: real AWS (read-only) when keys are present, else deterministic stub.

Credentials (AWS, decrypted JSON):
  Static keys: access_key_id, secret_access_key, optional session_token, optional region (default us-east-1).
  AssumeRole: auth_mode "assume_role", role_arn, optional external_id, optional role_session_name;
  delegate keys as delegate_access_key_id / delegate_secret_access_key (or reuse access_key_id / secret_access_key).

Never log credential values.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def _stub_graph(provider: str) -> Dict[str, Any]:
    """Deterministic demo graph when cloud APIs are not used (no keys or non-AWS)."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        "schema_version": 1,
        "captured_at": now,
        "provider": provider,
        "collection_mode": "stub",
        "resources": [
            {
                "id": "ec2:i-demo-stopped",
                "type": "ec2_instance",
                "region": "us-east-1",
                "name": "demo-idle",
                "tags": {"Environment": "dev"},
                "attributes": {"state": "stopped", "instance_type": "m5.2xlarge"},
            },
            {
                "id": "sg:sg-openssh",
                "type": "security_group",
                "region": "us-east-1",
                "name": "legacy-ssh",
                "tags": {},
                "attributes": {
                    "ingress": [
                        {"cidr": "0.0.0.0/0", "from_port": 22, "to_port": 22, "protocol": "tcp"}
                    ]
                },
            },
            {
                "id": "nat:nat-1",
                "type": "nat_gateway",
                "region": "us-east-1",
                "name": "single-nat",
                "tags": {},
                "attributes": {"availability_zone": "us-east-1a"},
            },
        ],
        "edges": [],
    }


def _region_from_availability_zone(az: str | None) -> str:
    if not az or len(az) < 2:
        return "unknown"
    return az[:-1] if az[-1].isalpha() else az  # us-east-1a -> us-east-1


def _normalize_ec2_ingress(permissions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Flatten boto3 IpPermissions into rule_engine-compatible ingress rows."""
    rows: List[Dict[str, Any]] = []
    for perm in permissions or []:
        proto = perm.get("IpProtocol") or "-1"
        from_port = perm.get("FromPort")
        to_port = perm.get("ToPort")
        for r in perm.get("IpRanges", []) or []:
            cidr = r.get("CidrIp")
            if cidr:
                rows.append(
                    {
                        "cidr": cidr,
                        "from_port": from_port,
                        "to_port": to_port,
                        "protocol": str(proto),
                    }
                )
        for r in perm.get("Ipv6Ranges", []) or []:
            cidr = r.get("CidrIpv6")
            if cidr:
                rows.append(
                    {
                        "cidr": cidr,
                        "from_port": from_port,
                        "to_port": to_port,
                        "protocol": str(proto),
                    }
                )
    return rows


def _cost_explorer_summary(
    ce_client: Any,
    *,
    lookback_days: int = 30,
) -> Dict[str, Any]:
    """
    Return account-level service cost summary using Cost Explorer (unblended monthly view).
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=lookback_days)
    resp = ce_client.get_cost_and_usage(
        TimePeriod={"Start": start_date.isoformat(), "End": end_date.isoformat()},
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"],
        GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
    )
    by_service: List[Dict[str, Any]] = []
    total = 0.0
    for period in resp.get("ResultsByTime", []) or []:
        for grp in period.get("Groups", []) or []:
            service = (grp.get("Keys") or ["Other"])[0]
            amount_raw = ((grp.get("Metrics") or {}).get("UnblendedCost") or {}).get("Amount", "0")
            try:
                amount = float(amount_raw)
            except (TypeError, ValueError):
                amount = 0.0
            total += amount
            by_service.append({"service": service, "unblended_cost_usd": round(amount, 2)})
    by_service.sort(key=lambda x: x["unblended_cost_usd"], reverse=True)

    def _pct(v: Any) -> float:
        try:
            return round(float(v), 2)
        except (TypeError, ValueError):
            return 0.0

    commitment_coverage = {
        "ec2_reservation_coverage_pct": 0.0,
        "ec2_savings_plan_coverage_pct": 0.0,
    }
    ec2_filter = {"Dimensions": {"Key": "SERVICE", "Values": ["Amazon Elastic Compute Cloud - Compute"]}}

    try:
        rc = ce_client.get_reservation_coverage(
            TimePeriod={"Start": start_date.isoformat(), "End": end_date.isoformat()},
            Granularity="MONTHLY",
            Filter=ec2_filter,
        )
        totals = rc.get("Total") or {}
        coverage_hours = totals.get("CoverageHours") or {}
        commitment_coverage["ec2_reservation_coverage_pct"] = _pct(
            coverage_hours.get("CoverageHoursPercentage")
        )
    except Exception:  # noqa: BLE001
        pass

    try:
        sp = ce_client.get_savings_plans_coverage(
            TimePeriod={"Start": start_date.isoformat(), "End": end_date.isoformat()},
            Granularity="MONTHLY",
            Filter=ec2_filter,
        )
        total = sp.get("Total") or {}
        coverage = total.get("Coverage") or {}
        commitment_coverage["ec2_savings_plan_coverage_pct"] = _pct(coverage.get("CoveragePercentage"))
    except Exception:  # noqa: BLE001
        pass

    return {
        "period_days": lookback_days,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "total_unblended_cost_usd": round(total, 2),
        "by_service": by_service,
        "commitment_coverage": commitment_coverage,
    }


def _metric_stats(datapoints: List[Dict[str, Any]]) -> Dict[str, float]:
    vals: List[float] = []
    for p in datapoints or []:
        avg = p.get("Average")
        if avg is None:
            continue
        try:
            vals.append(float(avg))
        except (TypeError, ValueError):
            continue
    if not vals:
        return {"avg": 0.0, "max": 0.0}
    return {"avg": round(sum(vals) / len(vals), 2), "max": round(max(vals), 2)}


def _metric_sum(datapoints: List[Dict[str, Any]], key: str = "Sum") -> float:
    total = 0.0
    for p in datapoints or []:
        v = p.get(key)
        if v is None:
            continue
        try:
            total += float(v)
        except (TypeError, ValueError):
            continue
    return round(total, 2)


def _assume_role_credentials(credentials: Dict[str, Any]) -> Dict[str, Any]:
    import boto3

    region = (credentials.get("region") or "us-east-1").strip()
    role_arn = (credentials.get("role_arn") or "").strip()
    if not role_arn:
        raise ValueError("role_arn is required when auth_mode is assume_role")

    base_ak = (credentials.get("delegate_access_key_id") or credentials.get("access_key_id") or "").strip()
    base_sk = (credentials.get("delegate_secret_access_key") or credentials.get("secret_access_key") or "").strip()
    tok = credentials.get("delegate_session_token") or credentials.get("session_token")
    tok = tok.strip() if isinstance(tok, str) else tok

    if not base_ak or not base_sk:
        raise ValueError(
            "assume_role requires delegate keys (delegate_access_key_id + delegate_secret_access_key, "
            "or access_key_id + secret_access_key) to call STS"
        )

    sts = boto3.client(
        "sts",
        region_name=region,
        aws_access_key_id=base_ak,
        aws_secret_access_key=base_sk,
        aws_session_token=tok or None,
    )
    session_name = (credentials.get("role_session_name") or "cloudcost-infra-intel").strip()[:64]
    kwargs: Dict[str, Any] = {"RoleArn": role_arn, "RoleSessionName": session_name or "cloudcost-infra-intel"}
    ext = credentials.get("external_id")
    if ext and str(ext).strip():
        kwargs["ExternalId"] = str(ext).strip()
    assumed = sts.assume_role(**kwargs)["Credentials"]
    return {
        "region": region,
        "aws_access_key_id": assumed["AccessKeyId"],
        "aws_secret_access_key": assumed["SecretAccessKey"],
        "aws_session_token": assumed["SessionToken"],
    }


def _static_key_credentials(credentials: Dict[str, Any]) -> Dict[str, Any]:
    region = (credentials.get("region") or "us-east-1").strip()
    ak = (credentials.get("access_key_id") or "").strip()
    sk = (credentials.get("secret_access_key") or "").strip()
    token = credentials.get("session_token")
    token = token.strip() if isinstance(token, str) else token
    return {
        "region": region,
        "aws_access_key_id": ak or None,
        "aws_secret_access_key": sk or None,
        "aws_session_token": token or None,
    }


def _resolve_aws_client_credentials(credentials: Dict[str, Any]) -> Dict[str, Any]:
    mode = (credentials.get("auth_mode") or "static_keys").strip().lower()
    if mode == "assume_role":
        return _assume_role_credentials(credentials)
    return _static_key_credentials(credentials)


def _sync_collect_aws(credentials: Dict[str, Any]) -> Dict[str, Any]:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError

    creds = _resolve_aws_client_credentials(credentials)
    region = creds["region"]
    ec2 = boto3.client(
        "ec2",
        region_name=region,
        aws_access_key_id=creds["aws_access_key_id"],
        aws_secret_access_key=creds["aws_secret_access_key"],
        aws_session_token=creds.get("aws_session_token"),
    )
    elbv2 = boto3.client(
        "elbv2",
        region_name=region,
        aws_access_key_id=creds["aws_access_key_id"],
        aws_secret_access_key=creds["aws_secret_access_key"],
        aws_session_token=creds.get("aws_session_token"),
    )
    eks = boto3.client(
        "eks",
        region_name=region,
        aws_access_key_id=creds["aws_access_key_id"],
        aws_secret_access_key=creds["aws_secret_access_key"],
        aws_session_token=creds.get("aws_session_token"),
    )
    rds = boto3.client(
        "rds",
        region_name=region,
        aws_access_key_id=creds["aws_access_key_id"],
        aws_secret_access_key=creds["aws_secret_access_key"],
        aws_session_token=creds.get("aws_session_token"),
    )
    ce = boto3.client(
        "ce",
        region_name="us-east-1",
        aws_access_key_id=creds["aws_access_key_id"],
        aws_secret_access_key=creds["aws_secret_access_key"],
        aws_session_token=creds.get("aws_session_token"),
    )
    cloudwatch = boto3.client(
        "cloudwatch",
        region_name=region,
        aws_access_key_id=creds["aws_access_key_id"],
        aws_secret_access_key=creds["aws_secret_access_key"],
        aws_session_token=creds.get("aws_session_token"),
    )
    ecs = boto3.client(
        "ecs",
        region_name=region,
        aws_access_key_id=creds["aws_access_key_id"],
        aws_secret_access_key=creds["aws_secret_access_key"],
        aws_session_token=creds.get("aws_session_token"),
    )
    lamb = boto3.client(
        "lambda",
        region_name=region,
        aws_access_key_id=creds["aws_access_key_id"],
        aws_secret_access_key=creds["aws_secret_access_key"],
        aws_session_token=creds.get("aws_session_token"),
    )
    s3 = boto3.client(
        "s3",
        aws_access_key_id=creds["aws_access_key_id"],
        aws_secret_access_key=creds["aws_secret_access_key"],
        aws_session_token=creds.get("aws_session_token"),
    )

    resources: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    collection_errors: List[Dict[str, str]] = []
    cost_summary: Dict[str, Any] = {"status": "unavailable", "reason": "not_collected"}

    try:
        paginator = ec2.get_paginator("describe_instances")
        for page in paginator.paginate():
            for rsv in page.get("Reservations", []):
                for inst in rsv.get("Instances", []):
                    iid = inst.get("InstanceId")
                    if not iid:
                        continue
                    az = (inst.get("Placement") or {}).get("AvailabilityZone")
                    reg = _region_from_availability_zone(az)
                    name = iid
                    for t in inst.get("Tags", []) or []:
                        if t.get("Key") == "Name" and t.get("Value"):
                            name = t["Value"]
                            break
                    state = (inst.get("State") or {}).get("Name", "unknown")
                    resources.append(
                        {
                            "id": f"ec2:{iid}",
                            "type": "ec2_instance",
                            "region": reg,
                            "name": name,
                            "tags": {t.get("Key"): t.get("Value") for t in (inst.get("Tags") or []) if t.get("Key")},
                            "attributes": {
                                "state": state,
                                "instance_type": inst.get("InstanceType", "unknown"),
                                "availability_zone": az,
                            },
                        }
                    )
                    try:
                        end_t = datetime.now(timezone.utc)
                        start_t = end_t - timedelta(days=14)
                        cpu = cloudwatch.get_metric_statistics(
                            Namespace="AWS/EC2",
                            MetricName="CPUUtilization",
                            Dimensions=[{"Name": "InstanceId", "Value": iid}],
                            StartTime=start_t,
                            EndTime=end_t,
                            Period=21600,
                            Statistics=["Average", "Maximum"],
                            Unit="Percent",
                        )
                        stats = _metric_stats(cpu.get("Datapoints") or [])
                        resources[-1]["attributes"]["cpu_avg_14d_pct"] = stats["avg"]
                        resources[-1]["attributes"]["cpu_max_14d_pct"] = stats["max"]
                    except (ClientError, BotoCoreError):
                        pass
                    for sg in inst.get("SecurityGroups", []) or []:
                        sgid = sg.get("GroupId")
                        if sgid:
                            edges.append(
                                {
                                    "from": f"ec2:{iid}",
                                    "to": f"sg:{sgid}",
                                    "rel": "uses_security_group",
                                }
                            )

        for page in ec2.get_paginator("describe_volumes").paginate():
            for vol in page.get("Volumes", []):
                vid = vol.get("VolumeId")
                if not vid:
                    continue
                attachments = vol.get("Attachments") or []
                reg = vol.get("AvailabilityZone", "")
                reg = _region_from_availability_zone(vol.get("AvailabilityZone"))
                resources.append(
                    {
                        "id": f"vol:{vid}",
                        "type": "ebs_volume",
                        "region": reg,
                        "name": vid,
                        "tags": {t.get("Key"): t.get("Value") for t in (vol.get("Tags") or []) if t.get("Key")},
                        "attributes": {
                            "state": vol.get("State", "unknown"),
                            "size_gb": vol.get("Size", 0),
                            "encrypted": vol.get("Encrypted", False),
                            "attachment_count": len(attachments),
                        },
                    }
                )

        for page in ec2.get_paginator("describe_security_groups").paginate():
            for sg in page.get("SecurityGroups", []):
                sgid = sg.get("GroupId")
                if not sgid:
                    continue
                vpc_id = sg.get("VpcId", "")
                ingress = _normalize_ec2_ingress(sg.get("IpPermissions", []))
                resources.append(
                    {
                        "id": f"sg:{sgid}",
                        "type": "security_group",
                        "region": region,
                        "name": sg.get("GroupName", sgid),
                        "tags": {t.get("Key"): t.get("Value") for t in (sg.get("Tags") or []) if t.get("Key")},
                        "attributes": {"vpc_id": vpc_id, "ingress": ingress},
                    }
                )

        for page in ec2.get_paginator("describe_nat_gateways").paginate():
            for nat in page.get("NatGateways", []):
                nid = nat.get("NatGatewayId")
                if not nid:
                    continue
                resources.append(
                    {
                        "id": f"nat:{nid}",
                        "type": "nat_gateway",
                        "region": region,
                        "name": nid,
                        "tags": {t.get("Key"): t.get("Value") for t in (nat.get("Tags") or []) if t.get("Key")},
                        "attributes": {
                            "state": nat.get("State", "unknown"),
                            "availability_zone": (nat.get("SubnetId") or "")[:20],
                        },
                    }
                )

        try:
            for page in elbv2.get_paginator("describe_load_balancers").paginate():
                for lb in page.get("LoadBalancers", []):
                    arn = lb.get("LoadBalancerArn", "")
                    lid = arn.split("/")[-1] if arn else lb.get("LoadBalancerName", "unknown")
                    azs = lb.get("AvailabilityZones") or []
                    z0 = azs[0].get("ZoneName") if azs else None
                    lb_region = _region_from_availability_zone(z0) if z0 else region
                    resources.append(
                        {
                            "id": f"alb:{lid}",
                            "type": "application_load_balancer",
                            "region": lb_region,
                            "name": lb.get("LoadBalancerName", lid),
                            "tags": {},
                            "attributes": {
                                "scheme": lb.get("Scheme", "unknown"),
                                "state": (lb.get("State") or {}).get("Code", "unknown"),
                                "load_balancer_type": lb.get("Type", "application"),
                            },
                        }
                    )
        except (ClientError, BotoCoreError) as exc:
            logger.warning("ELB collection failed", extra={"error": str(exc), "region": region})
            collection_errors.append({"service": "elbv2", "error": str(exc)})

        try:
            for c in eks.list_clusters().get("clusters", []) or []:
                desc = eks.describe_cluster(name=c).get("cluster", {})
                version = str(desc.get("version") or "unknown")
                arn = str(desc.get("arn") or "")
                cluster_id = arn.split("/")[-1] if arn else c
                resources.append(
                    {
                        "id": f"eks:{cluster_id}",
                        "type": "eks_cluster",
                        "region": region,
                        "name": desc.get("name", cluster_id),
                        "tags": desc.get("tags") or {},
                        "attributes": {
                            "version": version,
                            "status": desc.get("status", "unknown"),
                            "endpoint_public_access": bool(
                                ((desc.get("resourcesVpcConfig") or {}).get("endpointPublicAccess"))
                            ),
                        },
                    }
                )
                for ng in eks.list_nodegroups(clusterName=c).get("nodegroups", []) or []:
                    ngd = eks.describe_nodegroup(clusterName=c, nodegroupName=ng).get("nodegroup", {})
                    ng_id = f"{cluster_id}:{ng}"
                    scaling = ngd.get("scalingConfig") or {}
                    resources.append(
                        {
                            "id": f"eksng:{ng_id}",
                            "type": "eks_nodegroup",
                            "region": region,
                            "name": ng,
                            "tags": ngd.get("tags") or {},
                            "attributes": {
                                "cluster_name": c,
                                "status": ngd.get("status", "unknown"),
                                "instance_types": ngd.get("instanceTypes") or [],
                                "capacity_type": ngd.get("capacityType", "ON_DEMAND"),
                                "desired_size": int(scaling.get("desiredSize") or 0),
                                "min_size": int(scaling.get("minSize") or 0),
                                "max_size": int(scaling.get("maxSize") or 0),
                            },
                        }
                    )
                    edges.append({"from": f"eks:{cluster_id}", "to": f"eksng:{ng_id}", "rel": "has_nodegroup"})
        except (ClientError, BotoCoreError) as exc:
            logger.warning("EKS collection failed", extra={"error": str(exc), "region": region})
            collection_errors.append({"service": "eks", "error": str(exc)})

        try:
            for db in rds.describe_db_instances().get("DBInstances", []) or []:
                dbid = db.get("DBInstanceIdentifier")
                if not dbid:
                    continue
                resources.append(
                    {
                        "id": f"rds:{dbid}",
                        "type": "rds_instance",
                        "region": region,
                        "name": dbid,
                        "tags": {},
                        "attributes": {
                            "engine": db.get("Engine", "unknown"),
                            "engine_version": db.get("EngineVersion", "unknown"),
                            "instance_class": db.get("DBInstanceClass", "unknown"),
                            "multi_az": bool(db.get("MultiAZ", False)),
                            "storage_type": db.get("StorageType", "unknown"),
                            "allocated_storage_gb": int(db.get("AllocatedStorage") or 0),
                        },
                    }
                )
        except (ClientError, BotoCoreError) as exc:
            logger.warning("RDS collection failed", extra={"error": str(exc), "region": region})
            collection_errors.append({"service": "rds", "error": str(exc)})

        try:
            cluster_arns = ecs.list_clusters().get("clusterArns", []) or []
            for carn in cluster_arns:
                cname = carn.split("/")[-1]
                resources.append(
                    {
                        "id": f"ecs:{cname}",
                        "type": "ecs_cluster",
                        "region": region,
                        "name": cname,
                        "tags": {},
                        "attributes": {"cluster_arn": carn},
                    }
                )
                service_arns = ecs.list_services(cluster=carn).get("serviceArns", []) or []
                if service_arns:
                    for i in range(0, len(service_arns), 10):
                        desc = ecs.describe_services(cluster=carn, services=service_arns[i : i + 10]).get("services", [])
                        for svc in desc:
                            sname = str(svc.get("serviceName") or "unknown")
                            sid = f"{cname}:{sname}"
                            desired = int(svc.get("desiredCount") or 0)
                            running = int(svc.get("runningCount") or 0)
                            resources.append(
                                {
                                    "id": f"ecssvc:{sid}",
                                    "type": "ecs_service",
                                    "region": region,
                                    "name": sname,
                                    "tags": {},
                                    "attributes": {
                                        "cluster_name": cname,
                                        "launch_type": svc.get("launchType", "UNKNOWN"),
                                        "desired_count": desired,
                                        "running_count": running,
                                        "task_definition": svc.get("taskDefinition", ""),
                                    },
                                }
                            )
                            try:
                                end_t = datetime.now(timezone.utc)
                                start_t = end_t - timedelta(days=14)
                                cpu_m = cloudwatch.get_metric_statistics(
                                    Namespace="AWS/ECS",
                                    MetricName="CPUUtilization",
                                    Dimensions=[
                                        {"Name": "ClusterName", "Value": cname},
                                        {"Name": "ServiceName", "Value": sname},
                                    ],
                                    StartTime=start_t,
                                    EndTime=end_t,
                                    Period=21600,
                                    Statistics=["Average", "Maximum"],
                                    Unit="Percent",
                                )
                                mem_m = cloudwatch.get_metric_statistics(
                                    Namespace="AWS/ECS",
                                    MetricName="MemoryUtilization",
                                    Dimensions=[
                                        {"Name": "ClusterName", "Value": cname},
                                        {"Name": "ServiceName", "Value": sname},
                                    ],
                                    StartTime=start_t,
                                    EndTime=end_t,
                                    Period=21600,
                                    Statistics=["Average", "Maximum"],
                                    Unit="Percent",
                                )
                                cpu_stats = _metric_stats(cpu_m.get("Datapoints") or [])
                                mem_stats = _metric_stats(mem_m.get("Datapoints") or [])
                                resources[-1]["attributes"]["cpu_avg_14d_pct"] = cpu_stats["avg"]
                                resources[-1]["attributes"]["memory_avg_14d_pct"] = mem_stats["avg"]
                            except (ClientError, BotoCoreError):
                                pass
                            edges.append({"from": f"ecs:{cname}", "to": f"ecssvc:{sid}", "rel": "has_service"})
        except (ClientError, BotoCoreError) as exc:
            logger.warning("ECS collection failed", extra={"error": str(exc), "region": region})
            collection_errors.append({"service": "ecs", "error": str(exc)})

        try:
            paginator = lamb.get_paginator("list_functions")
            for page in paginator.paginate():
                for fn in page.get("Functions", []) or []:
                    fname = fn.get("FunctionName")
                    if not fname:
                        continue
                    resources.append(
                        {
                            "id": f"lambda:{fname}",
                            "type": "lambda_function",
                            "region": region,
                            "name": fname,
                            "tags": {},
                            "attributes": {
                                "runtime": fn.get("Runtime", "unknown"),
                                "memory_mb": int(fn.get("MemorySize") or 0),
                                "timeout_s": int(fn.get("Timeout") or 0),
                            },
                        }
                    )
                    try:
                        end_t = datetime.now(timezone.utc)
                        start_t = end_t - timedelta(days=14)
                        inv = cloudwatch.get_metric_statistics(
                            Namespace="AWS/Lambda",
                            MetricName="Invocations",
                            Dimensions=[{"Name": "FunctionName", "Value": fname}],
                            StartTime=start_t,
                            EndTime=end_t,
                            Period=86400,
                            Statistics=["Sum"],
                        )
                        dur = cloudwatch.get_metric_statistics(
                            Namespace="AWS/Lambda",
                            MetricName="Duration",
                            Dimensions=[{"Name": "FunctionName", "Value": fname}],
                            StartTime=start_t,
                            EndTime=end_t,
                            Period=86400,
                            Statistics=["Average", "Maximum"],
                            Unit="Milliseconds",
                        )
                        resources[-1]["attributes"]["invocations_14d"] = _metric_sum(inv.get("Datapoints") or [], "Sum")
                        resources[-1]["attributes"]["duration_avg_ms_14d"] = _metric_stats(dur.get("Datapoints") or [])["avg"]
                    except (ClientError, BotoCoreError):
                        pass
        except (ClientError, BotoCoreError) as exc:
            logger.warning("Lambda collection failed", extra={"error": str(exc), "region": region})
            collection_errors.append({"service": "lambda", "error": str(exc)})

        try:
            for b in s3.list_buckets().get("Buckets", []) or []:
                bname = b.get("Name")
                if not bname:
                    continue
                b_region = "us-east-1"
                lifecycle_rules = 0
                try:
                    loc = s3.get_bucket_location(Bucket=bname).get("LocationConstraint")
                    b_region = loc or "us-east-1"
                except (ClientError, BotoCoreError):
                    pass
                try:
                    lifecycle = s3.get_bucket_lifecycle_configuration(Bucket=bname)
                    lifecycle_rules = len(lifecycle.get("Rules") or [])
                except (ClientError, BotoCoreError):
                    lifecycle_rules = 0
                resources.append(
                    {
                        "id": f"s3:{bname}",
                        "type": "s3_bucket",
                        "region": b_region,
                        "name": bname,
                        "tags": {},
                        "attributes": {"lifecycle_rules": lifecycle_rules},
                    }
                )
        except (ClientError, BotoCoreError) as exc:
            logger.warning("S3 collection failed", extra={"error": str(exc)})
            collection_errors.append({"service": "s3", "error": str(exc)})

        try:
            cost_summary = _cost_explorer_summary(ce, lookback_days=30)
            cost_summary["status"] = "ok"
        except (ClientError, BotoCoreError, ValueError) as exc:
            logger.warning("Cost Explorer summary unavailable", extra={"error": str(exc)})
            cost_summary = {"status": "unavailable", "reason": str(exc)[:500]}
            collection_errors.append({"service": "cost_explorer", "error": str(exc)})

    except (ClientError, BotoCoreError) as exc:
        logger.warning("AWS collection failed", extra={"error": str(exc), "region": region})
        raise

    now = datetime.now(timezone.utc).isoformat()
    return {
        "schema_version": 1,
        "captured_at": now,
        "provider": "aws",
        "collection_mode": "aws_live",
        "region": region,
        "cost_summary": cost_summary,
        "collection_errors": collection_errors,
        "resources": resources,
        "edges": edges,
    }


def _aws_credentials_configured(credentials: Dict[str, Any]) -> bool:
    mode = (credentials.get("auth_mode") or "static_keys").strip().lower()
    if mode == "assume_role":
        if not (credentials.get("role_arn") or "").strip():
            return False
        ak = (credentials.get("delegate_access_key_id") or credentials.get("access_key_id") or "").strip()
        sk = (credentials.get("delegate_secret_access_key") or credentials.get("secret_access_key") or "").strip()
        return bool(ak and sk)
    ak = (credentials.get("access_key_id") or "").strip()
    sk = (credentials.get("secret_access_key") or "").strip()
    return bool(ak and sk)


async def collect_asset_graph(provider: str, credentials: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build normalized v1 graph. AWS uses API when access_key_id + secret_access_key are set.
    Otherwise returns a stub graph (demo / GCP / Azure until collectors exist).
    """
    if provider == "aws" and _aws_credentials_configured(credentials):
        return await asyncio.to_thread(_sync_collect_aws, credentials)
    return _stub_graph(provider)
