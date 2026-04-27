"""
Asset graph collection: real AWS (read-only) when keys are present, else deterministic stub.

Credentials (AWS, decrypted JSON):
  access_key_id, secret_access_key, optional session_token, optional region (default us-east-1).

Never log credential values.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
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


def _sync_collect_aws(credentials: Dict[str, Any]) -> Dict[str, Any]:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError

    region = (credentials.get("region") or "us-east-1").strip()
    ak = (credentials.get("access_key_id") or "").strip()
    sk = (credentials.get("secret_access_key") or "").strip()
    token = credentials.get("session_token")
    token = token.strip() if isinstance(token, str) else token

    ec2 = boto3.client(
        "ec2",
        region_name=region,
        aws_access_key_id=ak or None,
        aws_secret_access_key=sk or None,
        aws_session_token=token or None,
    )
    elbv2 = boto3.client(
        "elbv2",
        region_name=region,
        aws_access_key_id=ak or None,
        aws_secret_access_key=sk or None,
        aws_session_token=token or None,
    )

    resources: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []

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
        logger.warning("AWS collection failed", extra={"error": str(exc), "region": region})
        raise

    now = datetime.now(timezone.utc).isoformat()
    return {
        "schema_version": 1,
        "captured_at": now,
        "provider": "aws",
        "collection_mode": "aws_live",
        "region": region,
        "resources": resources,
        "edges": edges,
    }


def _aws_credentials_configured(credentials: Dict[str, Any]) -> bool:
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
