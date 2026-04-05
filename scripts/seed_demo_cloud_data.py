#!/usr/bin/env python3
"""
Seed minimal demo CloudInstance + CloudPricing rows so the UI works offline
(Instance Finder, Spot Intelligence) without running full AWS/GCP/Azure fetchers.

Run after migrations:
  source venv/bin/activate && python scripts/seed_demo_cloud_data.py
"""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from src.core.database import get_db_context
from src.models.cloud_provider import CloudInstance, CloudPricing


DEMO_INSTANCES = [
    # provider, type, family, vcpus, mem, category
    ("aws", "t3.micro", "t3", 2, 1.0, "general_purpose"),
    ("aws", "m5.large", "m5", 2, 8.0, "general_purpose"),
    ("aws", "m5.xlarge", "m5", 4, 16.0, "general_purpose"),
    ("aws", "c5.large", "c5", 2, 4.0, "compute_optimized"),
    ("gcp", "n1-standard-2", "n1", 2, 7.5, "general_purpose"),
    ("gcp", "n2-standard-4", "n2", 4, 16.0, "general_purpose"),
    ("azure", "Standard_B2s", "B", 2, 4.0, "general_purpose"),
    ("azure", "Standard_D4s_v5", "D", 4, 16.0, "general_purpose"),
]

# (provider, instance_type, region, pricing_type, hourly)
DEMO_PRICING = [
    ("aws", "t3.micro", "us-east-1", "on_demand", "0.0104"),
    ("aws", "m5.large", "us-east-1", "on_demand", "0.096"),
    ("aws", "m5.xlarge", "us-east-1", "on_demand", "0.192"),
    ("aws", "m5.xlarge", "us-east-1", "spot", "0.048"),
    ("aws", "m5.xlarge", "us-west-2", "spot", "0.052"),
    ("aws", "c5.large", "us-east-1", "on_demand", "0.085"),
    ("gcp", "n1-standard-2", "us-central1", "on_demand", "0.095"),
    ("gcp", "n2-standard-4", "us-central1", "on_demand", "0.194"),
    ("gcp", "n1-standard-2", "us-central1", "preemptible", "0.032"),
    ("azure", "Standard_B2s", "eastus", "on_demand", "0.0416"),
    ("azure", "Standard_D4s_v5", "eastus", "on_demand", "0.192"),
]


async def main() -> None:
    async with get_db_context() as db:
        r = await db.execute(select(func.count()).select_from(CloudInstance))
        existing = r.scalar() or 0
        if existing >= 50:
            print(f"cloud_instances already has {existing} rows — skip demo seed (use --force to add anyway).")
            if "--force" not in sys.argv:
                return

    inserted_i = 0
    inserted_p = 0

    async with get_db_context() as db:
        for provider, itype, family, vcpus, mem, cat in DEMO_INSTANCES:
            stmt = (
                pg_insert(CloudInstance)
                .values(
                    provider=provider,
                    instance_type=itype,
                    instance_family=family,
                    display_name=f"{itype}",
                    vcpus=vcpus,
                    memory_gb=mem,
                    processor_architecture="x86_64",
                    storage_type="SSD",
                    category=cat,
                    is_burstable=itype.startswith("t3") or itype.startswith("Standard_B"),
                    supports_spot=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                .on_conflict_do_nothing(constraint="uq_cloud_instance")
            )
            res = await db.execute(stmt)
            if res.rowcount:
                inserted_i += 1

        for provider, itype, region, ptype, hourly in DEMO_PRICING:
            stmt = (
                pg_insert(CloudPricing)
                .values(
                    provider=provider,
                    instance_type=itype,
                    region=region,
                    zone=None,
                    pricing_type=ptype,
                    os_type="linux",
                    hourly_price=Decimal(hourly),
                    currency="USD",
                    effective_date=datetime.utcnow(),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                .on_conflict_do_nothing(constraint="uq_cloud_pricing")
            )
            res = await db.execute(stmt)
            if res.rowcount:
                inserted_p += 1

    print(f"Demo seed done: +{inserted_i} instances, +{inserted_p} pricing rows (skipped duplicates).")


if __name__ == "__main__":
    asyncio.run(main())
