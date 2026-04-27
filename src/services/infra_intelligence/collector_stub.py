"""
Stub collector producing a normalized asset graph for development and tests.

Replace with real AWS/GCP/Azure collectors that call cloud APIs with decrypted credentials.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict


def build_stub_graph(provider: str) -> Dict[str, Any]:
    """Return schema_version 1 graph with sample resources for rule demos."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        "schema_version": 1,
        "captured_at": now,
        "provider": provider,
        "resources": [
            {
                "id": "ec2:i-0deadbeef1",
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
        "edges": [
            {"from": "ec2:i-0deadbeef1", "to": "sg:sg-openssh", "rel": "uses_security_group"},
            {"from": "nat:nat-1", "to": "ec2:i-0deadbeef1", "rel": "routes_through"},
        ],
    }
