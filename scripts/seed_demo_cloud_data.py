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
    ("aws", "r5.large", "r5", 2, 16.0, "memory_optimized"),
    # GCP — broader catalog for multi-cloud users
    ("gcp", "n1-standard-2", "n1", 2, 7.5, "general_purpose"),
    ("gcp", "n1-standard-4", "n1", 4, 15.0, "general_purpose"),
    ("gcp", "n2-standard-4", "n2", 4, 16.0, "general_purpose"),
    ("gcp", "n2-standard-8", "n2", 8, 32.0, "general_purpose"),
    ("gcp", "n2d-standard-4", "n2d", 4, 16.0, "general_purpose"),
    ("gcp", "e2-standard-2", "e2", 2, 8.0, "general_purpose"),
    ("gcp", "e2-standard-4", "e2", 4, 16.0, "general_purpose"),
    ("gcp", "c2-standard-4", "c2", 4, 16.0, "compute_optimized"),
    ("gcp", "n2-highmem-4", "n2", 4, 32.0, "memory_optimized"),
    # Azure — D/E/F/B families
    ("azure", "Standard_B2s", "B", 2, 4.0, "general_purpose"),
    ("azure", "Standard_B2ms", "B", 2, 8.0, "general_purpose"),
    ("azure", "Standard_D2s_v5", "D", 2, 8.0, "general_purpose"),
    ("azure", "Standard_D4s_v5", "D", 4, 16.0, "general_purpose"),
    ("azure", "Standard_D8s_v5", "D", 8, 32.0, "general_purpose"),
    ("azure", "Standard_E4s_v5", "E", 4, 32.0, "memory_optimized"),
    ("azure", "Standard_E8s_v5", "E", 8, 64.0, "memory_optimized"),
    ("azure", "Standard_F4s_v2", "F", 4, 8.0, "compute_optimized"),
    # Extra GCP (helps balance vs heavy AWS ingest)
    ("gcp", "n2-standard-2", "n2", 2, 8.0, "general_purpose"),
    ("gcp", "n2-standard-16", "n2", 16, 64.0, "general_purpose"),
    ("gcp", "n2d-standard-8", "n2d", 8, 32.0, "general_purpose"),
    ("gcp", "n2d-standard-16", "n2d", 16, 64.0, "general_purpose"),
    ("gcp", "e2-medium", "e2", 2, 4.0, "general_purpose"),
    ("gcp", "e2-standard-8", "e2", 8, 32.0, "general_purpose"),
    ("gcp", "t2d-standard-2", "t2d", 2, 8.0, "general_purpose"),
    ("gcp", "t2d-standard-4", "t2d", 4, 16.0, "general_purpose"),
    ("gcp", "c2-standard-8", "c2", 8, 32.0, "compute_optimized"),
    ("gcp", "n2-highmem-8", "n2", 8, 64.0, "memory_optimized"),
    # Extra Azure
    ("azure", "Standard_D16s_v5", "D", 16, 64.0, "general_purpose"),
    ("azure", "Standard_D32s_v5", "D", 32, 128.0, "general_purpose"),
    ("azure", "Standard_E16s_v5", "E", 16, 128.0, "memory_optimized"),
    ("azure", "Standard_E32s_v5", "E", 32, 256.0, "memory_optimized"),
    ("azure", "Standard_F8s_v2", "F", 8, 16.0, "compute_optimized"),
    ("azure", "Standard_F16s_v2", "F", 16, 32.0, "compute_optimized"),
    ("azure", "Standard_B4ms", "B", 4, 16.0, "general_purpose"),
    ("azure", "Standard_B8ms", "B", 8, 32.0, "general_purpose"),
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
    ("gcp", "n2-standard-4", "us-central1", "preemptible", "0.055"),
    ("azure", "Standard_B2s", "eastus", "on_demand", "0.0416"),
    ("azure", "Standard_D4s_v5", "eastus", "on_demand", "0.192"),
    ("azure", "Standard_D4s_v5", "eastus", "spot", "0.058"),
    ("aws", "c5.large", "us-east-1", "spot", "0.034"),
    ("aws", "r5.large", "us-east-1", "on_demand", "0.126"),
    # GCP pricing (representative — ingest real rates in production)
    ("gcp", "n1-standard-4", "us-central1", "on_demand", "0.190"),
    ("gcp", "n2-standard-8", "us-central1", "on_demand", "0.388"),
    ("gcp", "n2d-standard-4", "us-central1", "on_demand", "0.185"),
    ("gcp", "e2-standard-2", "us-central1", "on_demand", "0.067"),
    ("gcp", "e2-standard-4", "us-central1", "on_demand", "0.134"),
    ("gcp", "c2-standard-4", "us-central1", "on_demand", "0.210"),
    ("gcp", "n2-highmem-4", "us-central1", "on_demand", "0.262"),
    ("gcp", "n1-standard-4", "us-central1", "preemptible", "0.057"),
    ("gcp", "n2-standard-8", "us-central1", "preemptible", "0.116"),
    ("gcp", "e2-standard-4", "europe-west1", "on_demand", "0.138"),
    # Azure pricing
    ("azure", "Standard_D2s_v5", "eastus", "on_demand", "0.096"),
    ("azure", "Standard_D8s_v5", "eastus", "on_demand", "0.384"),
    ("azure", "Standard_B2ms", "eastus", "on_demand", "0.083"),
    ("azure", "Standard_E4s_v5", "eastus", "on_demand", "0.252"),
    ("azure", "Standard_E8s_v5", "eastus", "on_demand", "0.504"),
    ("azure", "Standard_F4s_v2", "eastus", "on_demand", "0.166"),
    ("azure", "Standard_D2s_v5", "westus2", "spot", "0.038"),
    ("azure", "Standard_D8s_v5", "eastus", "spot", "0.154"),
    # Extra GCP / Azure on-demand + spot (us-central1 / eastus)
    ("gcp", "n2-standard-2", "us-central1", "on_demand", "0.097"),
    ("gcp", "n2-standard-16", "us-central1", "on_demand", "0.776"),
    ("gcp", "n2d-standard-8", "us-central1", "on_demand", "0.370"),
    ("gcp", "e2-medium", "us-central1", "on_demand", "0.034"),
    ("gcp", "e2-standard-8", "us-central1", "on_demand", "0.268"),
    ("gcp", "t2d-standard-4", "us-central1", "on_demand", "0.124"),
    ("gcp", "c2-standard-8", "us-central1", "on_demand", "0.420"),
    ("gcp", "n2-highmem-8", "us-central1", "on_demand", "0.524"),
    ("gcp", "n2-standard-2", "us-central1", "preemptible", "0.029"),
    ("azure", "Standard_D16s_v5", "eastus", "on_demand", "0.768"),
    ("azure", "Standard_D32s_v5", "eastus", "on_demand", "1.536"),
    ("azure", "Standard_E16s_v5", "eastus", "on_demand", "1.008"),
    ("azure", "Standard_F8s_v2", "eastus", "on_demand", "0.332"),
    ("azure", "Standard_B4ms", "eastus", "on_demand", "0.166"),
    ("azure", "Standard_D16s_v5", "eastus", "spot", "0.308"),
]


async def main() -> None:
    async with get_db_context() as db:
        r = await db.execute(select(func.count()).select_from(CloudInstance))
        existing = r.scalar() or 0
        skip_instances = existing >= 50 and "--force" not in sys.argv
        if skip_instances:
            print(
                f"cloud_instances has {existing} rows — skipping demo instance rows "
                f"(use --force to insert demo instances). Still merging demo pricing for Spot AI / UI."
            )

    inserted_i = 0
    inserted_p = 0

    async with get_db_context() as db:
        if not skip_instances:
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
