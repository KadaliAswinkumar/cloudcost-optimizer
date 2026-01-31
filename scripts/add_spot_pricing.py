#!/usr/bin/env python3
"""
Add Spot/Preemptible Pricing Data
Generates realistic spot pricing (60-90% cheaper than on-demand)
"""

import asyncio
import logging
import random
from decimal import Decimal
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Generate spot pricing for all existing on-demand instances."""
    from src.core.database import get_db_context
    from src.models.cloud_provider import CloudPricing
    from sqlalchemy import select, delete
    
    print("\n" + "="*70)
    print("⚡ ADDING SPOT/PREEMPTIBLE PRICING")
    print("="*70 + "\n")
    
    stats = {
        "aws_spot": 0,
        "gcp_preemptible": 0,
        "azure_spot": 0,
        "total": 0
    }
    
    # 1. Clear existing spot/preemptible pricing
    print("🧹 Clearing existing spot pricing...")
    async with get_db_context() as db:
        await db.execute(
            delete(CloudPricing).where(
                CloudPricing.pricing_type.in_(["spot", "preemptible"])
            )
        )
        await db.commit()
        logger.info("✓ Cleared existing spot/preemptible pricing")
    
    # 2. Get all on-demand pricing
    print("📊 Fetching on-demand pricing...")
    async with get_db_context() as db:
        result = await db.execute(
            select(CloudPricing).where(
                CloudPricing.pricing_type == "on_demand"
            )
        )
        on_demand_prices = result.scalars().all()
        logger.info(f"Found {len(on_demand_prices)} on-demand prices")
    
    # 3. Generate spot pricing for each on-demand price
    print("⚡ Generating spot pricing...")
    spot_prices = []
    
    for od_price in on_demand_prices:
        # Determine spot type based on provider
        if od_price.provider == "aws":
            spot_type = "spot"
        elif od_price.provider == "gcp":
            spot_type = "preemptible"
        elif od_price.provider == "azure":
            spot_type = "spot"
        else:
            continue
        
        # Generate realistic spot discount (60-90% cheaper)
        # Different regions have different volatility
        discount_factor = random.uniform(0.10, 0.40)  # 60-90% off
        spot_hourly = float(od_price.hourly_price) * discount_factor
        
        # Add some regional variance
        # Some regions are cheaper than others
        regional_variance = random.uniform(-0.05, 0.15)  # -5% to +15%
        spot_hourly = spot_hourly * (1 + regional_variance)
        
        # Ensure minimum price (can't be free)
        spot_hourly = max(spot_hourly, 0.0001)
        
        spot_monthly = spot_hourly * 730
        
        # Create spot pricing record
        spot_price = CloudPricing(
            provider=od_price.provider,
            instance_type=od_price.instance_type,
            region=od_price.region,
            zone=od_price.zone,
            pricing_type=spot_type,
            os_type=od_price.os_type,
            hourly_price=Decimal(str(round(spot_hourly, 6))),
            monthly_price=Decimal(str(round(spot_monthly, 2))),
            currency=od_price.currency,
            effective_date=datetime.utcnow()
        )
        
        spot_prices.append(spot_price)
        
        if od_price.provider == "aws":
            stats["aws_spot"] += 1
        elif od_price.provider == "gcp":
            stats["gcp_preemptible"] += 1
        elif od_price.provider == "azure":
            stats["azure_spot"] += 1
    
    # 4. Bulk insert spot pricing
    print(f"💾 Inserting {len(spot_prices)} spot prices...")
    async with get_db_context() as db:
        # Insert in batches to avoid memory issues
        batch_size = 500
        for i in range(0, len(spot_prices), batch_size):
            batch = spot_prices[i:i + batch_size]
            db.add_all(batch)
            await db.commit()
            logger.info(f"Inserted batch {i//batch_size + 1} ({len(batch)} prices)")
    
    stats["total"] = len(spot_prices)
    
    print("\n" + "="*70)
    print("✅ SPOT PRICING GENERATION COMPLETE")
    print("="*70)
    print(f"\n📊 Statistics:")
    print(f"   AWS Spot:              {stats['aws_spot']:,}")
    print(f"   GCP Preemptible:       {stats['gcp_preemptible']:,}")
    print(f"   Azure Spot:            {stats['azure_spot']:,}")
    print(f"   ────────────────────────────────")
    print(f"   TOTAL SPOT PRICES:     {stats['total']:,}")
    print("\n" + "="*70)
    print("⚡ Spot Intelligence™ is now ready!")
    print("   Try: AWS m5.xlarge, GCP n2-standard-4, Azure Standard_D4s_v3")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
