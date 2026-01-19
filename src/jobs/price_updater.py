"""
Price Updater Tasks
Background tasks for fetching and updating AWS pricing data.
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Optional

from celery import shared_task
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from src.jobs.celery_app import celery_app
from src.core.config import settings
from src.core.database import get_db_context
from src.services.aws_price_fetcher import AWSPriceFetcher
from src.models.instance import EC2Instance
from src.models.pricing import OnDemandPricing, SpotPricing

logger = logging.getLogger(__name__)


def run_async(coro):
    """Helper to run async code in Celery tasks."""
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # Create a new loop if one is already running
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@celery_app.task(
    bind=True,
    name="src.jobs.price_updater.update_all_prices",
    max_retries=3,
    default_retry_delay=300,
)
def update_all_prices(self, regions: Optional[List[str]] = None):
    """
    Update all pricing data for specified regions.
    
    Args:
        regions: List of AWS regions (defaults to all configured)
        
    Returns:
        Summary of update results
    """
    logger.info("Starting full price update...")
    
    regions = regions or settings.aws_regions
    results = {
        "started_at": datetime.utcnow().isoformat(),
        "regions_processed": 0,
        "instances_updated": 0,
        "prices_updated": 0,
        "errors": [],
    }
    
    try:
        # Update instance types first
        instances_count = run_async(_update_instance_types())
        results["instances_updated"] = instances_count
        
        # Update pricing for each region
        for region in regions:
            try:
                prices_count = run_async(_update_region_pricing(region))
                results["prices_updated"] += prices_count
                results["regions_processed"] += 1
                logger.info(f"Updated {prices_count} prices for {region}")
            except Exception as e:
                error_msg = f"Error updating {region}: {str(e)}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
        
        results["completed_at"] = datetime.utcnow().isoformat()
        results["success"] = len(results["errors"]) == 0
        
        logger.info(f"Price update complete: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Price update failed: {e}")
        self.retry(exc=e)


@celery_app.task(
    bind=True,
    name="src.jobs.price_updater.update_region_prices",
    max_retries=3,
    default_retry_delay=60,
)
def update_region_prices(self, region: str):
    """
    Update pricing for a specific region.
    
    Args:
        region: AWS region code
        
    Returns:
        Number of prices updated
    """
    logger.info(f"Updating prices for region: {region}")
    
    try:
        count = run_async(_update_region_pricing(region))
        logger.info(f"Updated {count} prices for {region}")
        return {"region": region, "prices_updated": count}
    except Exception as e:
        logger.error(f"Failed to update {region}: {e}")
        self.retry(exc=e)


async def _update_instance_types() -> int:
    """Fetch and update EC2 instance types."""
    fetcher = AWSPriceFetcher()
    instances = await fetcher.fetch_instance_types()
    
    async with get_db_context() as db:
        count = 0
        for instance_data in instances:
            stmt = insert(EC2Instance).values(**instance_data)
            stmt = stmt.on_conflict_do_update(
                index_elements=["instance_type"],
                set_={
                    "vcpus": instance_data["vcpus"],
                    "memory_gb": instance_data["memory_gb"],
                    "network_performance": instance_data["network_performance"],
                    "current_generation": instance_data["current_generation"],
                    "updated_at": datetime.utcnow(),
                },
            )
            await db.execute(stmt)
            count += 1
        
        await db.commit()
    
    return count


async def _update_region_pricing(region: str) -> int:
    """Update pricing for a specific region."""
    fetcher = AWSPriceFetcher()
    
    # Fetch on-demand pricing
    on_demand_prices = await fetcher.fetch_on_demand_pricing(region)
    
    # Fetch spot pricing
    spot_prices = await fetcher.fetch_spot_prices(region)
    
    count = 0
    
    async with get_db_context() as db:
        # Update on-demand prices
        for price_data in on_demand_prices:
            stmt = insert(OnDemandPricing).values(
                instance_type=price_data["instance_type"],
                region=price_data["region"],
                price_per_hour=price_data["price_per_hour"],
                operating_system=price_data["operating_system"],
                tenancy=price_data["tenancy"],
                effective_date=price_data["effective_date"],
            )
            stmt = stmt.on_conflict_do_update(
                constraint="uq_ondemand_pricing",
                set_={
                    "price_per_hour": price_data["price_per_hour"],
                    "effective_date": price_data["effective_date"],
                    "updated_at": datetime.utcnow(),
                },
            )
            await db.execute(stmt)
            count += 1
        
        # Update spot prices
        for price_data in spot_prices:
            stmt = insert(SpotPricing).values(
                instance_type=price_data["instance_type"],
                region=price_data["region"],
                availability_zone=price_data["availability_zone"],
                spot_price=price_data["spot_price"],
                timestamp=price_data["timestamp"],
            )
            stmt = stmt.on_conflict_do_update(
                constraint="uq_spot_pricing",
                set_={
                    "spot_price": price_data["spot_price"],
                    "timestamp": price_data["timestamp"],
                    "updated_at": datetime.utcnow(),
                },
            )
            await db.execute(stmt)
            count += 1
        
        await db.commit()
    
    return count


@celery_app.task(name="src.jobs.price_updater.seed_sample_data")
def seed_sample_data():
    """
    Seed database with sample data for development/testing.
    
    This creates realistic sample data without requiring AWS credentials.
    """
    logger.info("Seeding sample data...")
    run_async(_seed_sample_data())
    logger.info("Sample data seeded successfully")


async def _seed_sample_data():
    """Create sample instance and pricing data."""
    from decimal import Decimal
    
    # Sample instance types
    sample_instances = [
        {"instance_type": "t3.micro", "instance_family": "t3", "vcpus": 2, "memory_gb": 1.0, "network_performance": "Low to Moderate"},
        {"instance_type": "t3.small", "instance_family": "t3", "vcpus": 2, "memory_gb": 2.0, "network_performance": "Low to Moderate"},
        {"instance_type": "t3.medium", "instance_family": "t3", "vcpus": 2, "memory_gb": 4.0, "network_performance": "Low to Moderate"},
        {"instance_type": "t3.large", "instance_family": "t3", "vcpus": 2, "memory_gb": 8.0, "network_performance": "Low to Moderate"},
        {"instance_type": "m5.large", "instance_family": "m5", "vcpus": 2, "memory_gb": 8.0, "network_performance": "Up to 10 Gigabit"},
        {"instance_type": "m5.xlarge", "instance_family": "m5", "vcpus": 4, "memory_gb": 16.0, "network_performance": "Up to 10 Gigabit"},
        {"instance_type": "m5.2xlarge", "instance_family": "m5", "vcpus": 8, "memory_gb": 32.0, "network_performance": "Up to 10 Gigabit"},
        {"instance_type": "c5.large", "instance_family": "c5", "vcpus": 2, "memory_gb": 4.0, "network_performance": "Up to 10 Gigabit"},
        {"instance_type": "c5.xlarge", "instance_family": "c5", "vcpus": 4, "memory_gb": 8.0, "network_performance": "Up to 10 Gigabit"},
        {"instance_type": "r5.large", "instance_family": "r5", "vcpus": 2, "memory_gb": 16.0, "network_performance": "Up to 10 Gigabit"},
    ]
    
    # Sample pricing (approximate)
    sample_pricing = {
        "t3.micro": {"us-east-1": 0.0104, "us-west-2": 0.0104, "eu-west-1": 0.0114},
        "t3.small": {"us-east-1": 0.0208, "us-west-2": 0.0208, "eu-west-1": 0.0228},
        "t3.medium": {"us-east-1": 0.0416, "us-west-2": 0.0416, "eu-west-1": 0.0456},
        "t3.large": {"us-east-1": 0.0832, "us-west-2": 0.0832, "eu-west-1": 0.0912},
        "m5.large": {"us-east-1": 0.096, "us-west-2": 0.096, "eu-west-1": 0.107},
        "m5.xlarge": {"us-east-1": 0.192, "us-west-2": 0.192, "eu-west-1": 0.214},
        "m5.2xlarge": {"us-east-1": 0.384, "us-west-2": 0.384, "eu-west-1": 0.428},
        "c5.large": {"us-east-1": 0.085, "us-west-2": 0.085, "eu-west-1": 0.096},
        "c5.xlarge": {"us-east-1": 0.170, "us-west-2": 0.170, "eu-west-1": 0.192},
        "r5.large": {"us-east-1": 0.126, "us-west-2": 0.126, "eu-west-1": 0.141},
    }
    
    async with get_db_context() as db:
        # Insert instances
        for inst in sample_instances:
            inst["processor_architecture"] = "x86_64"
            inst["current_generation"] = True
            inst["storage_type"] = "EBS-Only"
            
            stmt = insert(EC2Instance).values(**inst)
            stmt = stmt.on_conflict_do_nothing()
            await db.execute(stmt)
        
        # Insert pricing
        for instance_type, regions in sample_pricing.items():
            for region, price in regions.items():
                # On-Demand
                stmt = insert(OnDemandPricing).values(
                    instance_type=instance_type,
                    region=region,
                    price_per_hour=Decimal(str(price)),
                    operating_system="Linux",
                    tenancy="Shared",
                    effective_date=datetime.utcnow(),
                )
                stmt = stmt.on_conflict_do_nothing()
                await db.execute(stmt)
                
                # Spot (roughly 30-70% of on-demand)
                import random
                spot_price = price * random.uniform(0.3, 0.7)
                for az_suffix in ["a", "b", "c"]:
                    stmt = insert(SpotPricing).values(
                        instance_type=instance_type,
                        region=region,
                        availability_zone=f"{region}{az_suffix}",
                        spot_price=Decimal(str(round(spot_price, 6))),
                        timestamp=datetime.utcnow(),
                    )
                    stmt = stmt.on_conflict_do_nothing()
                    await db.execute(stmt)
        
        await db.commit()

