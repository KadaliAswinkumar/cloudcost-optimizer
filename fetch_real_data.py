#!/usr/bin/env python3
"""
Fetch Real Cloud Pricing Data
Fetches live pricing from AWS, GCP, and Azure APIs
"""

import asyncio
import logging
import sys
from datetime import datetime
from decimal import Decimal
from typing import List, Dict

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main function to fetch all cloud data."""
    from src.core.database import get_db_context
    from src.models.cloud_provider import CloudInstance, CloudProvider
    from src.services.aws_price_fetcher import AWSPriceFetcher
    from src.services.gcp_price_fetcher import GCPPriceFetcher
    from src.services.azure_price_fetcher import AzurePriceFetcher
    
    print("\n" + "="*70)
    print("🌐 FETCHING REAL CLOUD PRICING DATA")
    print("="*70 + "\n")
    
    stats = {
        "aws": {"instances": 0, "pricing": 0},
        "gcp": {"instances": 0, "pricing": 0},
        "azure": {"instances": 0, "pricing": 0},
        "total_time": 0,
        "errors": []
    }
    
    start_time = datetime.now()
    
    # ==================== AWS ====================
    print("📊 1/3 Fetching AWS EC2 Data...")
    print("-" * 70)
    try:
        aws_fetcher = AWSPriceFetcher()
        
        # Fetch from multiple regions
        aws_regions = ["us-east-1", "us-west-2", "eu-west-1"]
        
        for region in aws_regions:
            logger.info(f"Fetching AWS data for region: {region}")
            
            # Fetch on-demand pricing
            pricing_data = await aws_fetcher.fetch_on_demand_pricing(region)
            
            async with get_db_context() as db:
                for price_info in pricing_data:
                    # Insert instance
                    instance_data = {
                        "provider": "aws",
                        "instance_type": price_info["instance_type"],
                        "vcpus": price_info.get("vcpus", 0),
                        "memory_gb": price_info.get("memory_gb", 0),
                        "network_performance": price_info.get("network_performance", "Unknown"),
                        "region": region,
                        "price_per_hour": Decimal(str(price_info["price_per_hour"])),
                        "operating_system": price_info.get("operating_system", "Linux"),
                        "spot_available": True,
                        "metadata": {
                            "tenancy": price_info.get("tenancy", "Shared"),
                            "processor_architecture": "x86_64",
                        }
                    }
                    
                    stmt = insert(CloudInstance).values(**instance_data)
                    stmt = stmt.on_conflict_do_update(
                        index_elements=["provider", "instance_type", "region"],
                        set_={
                            "price_per_hour": instance_data["price_per_hour"],
                            "updated_at": datetime.utcnow(),
                        }
                    )
                    await db.execute(stmt)
                    stats["aws"]["instances"] += 1
                
                await db.commit()
            
            logger.info(f"✓ AWS {region}: {len(pricing_data)} instances")
        
        print(f"✅ AWS: {stats['aws']['instances']} instances fetched")
        
    except Exception as e:
        error_msg = f"AWS fetch failed: {str(e)}"
        logger.error(error_msg)
        stats["errors"].append(error_msg)
        print(f"❌ AWS failed: {str(e)}")
    
    # ==================== GCP ====================
    print("\n📊 2/3 Fetching GCP Compute Engine Data...")
    print("-" * 70)
    try:
        gcp_fetcher = GCPPriceFetcher()
        
        # Fetch from multiple regions
        gcp_regions = ["us-central1", "us-west1", "europe-west1"]
        
        for region in gcp_regions:
            logger.info(f"Fetching GCP data for region: {region}")
            
            pricing_data = await gcp_fetcher.fetch_pricing(region)
            
            async with get_db_context() as db:
                for price_info in pricing_data:
                    instance_data = {
                        "provider": "gcp",
                        "instance_type": price_info["instance_type"],
                        "vcpus": price_info.get("vcpus", 0),
                        "memory_gb": price_info.get("memory_gb", 0),
                        "network_performance": "Standard",
                        "region": region,
                        "price_per_hour": Decimal(str(price_info["price_per_hour"])),
                        "operating_system": "Linux",
                        "spot_available": price_info.get("spot_available", True),
                        "metadata": {
                            "machine_family": price_info.get("machine_family", "general"),
                        }
                    }
                    
                    stmt = insert(CloudInstance).values(**instance_data)
                    stmt = stmt.on_conflict_do_update(
                        index_elements=["provider", "instance_type", "region"],
                        set_={
                            "price_per_hour": instance_data["price_per_hour"],
                            "updated_at": datetime.utcnow(),
                        }
                    )
                    await db.execute(stmt)
                    stats["gcp"]["instances"] += 1
                
                await db.commit()
            
            logger.info(f"✓ GCP {region}: {len(pricing_data)} instances")
        
        print(f"✅ GCP: {stats['gcp']['instances']} instances fetched")
        
    except Exception as e:
        error_msg = f"GCP fetch failed: {str(e)}"
        logger.error(error_msg)
        stats["errors"].append(error_msg)
        print(f"❌ GCP failed: {str(e)}")
    
    # ==================== AZURE ====================
    print("\n📊 3/3 Fetching Azure Virtual Machines Data...")
    print("-" * 70)
    try:
        azure_fetcher = AzurePriceFetcher()
        
        # Fetch from multiple regions
        azure_regions = ["eastus", "westus2", "westeurope"]
        
        for region in azure_regions:
            logger.info(f"Fetching Azure data for region: {region}")
            
            pricing_data = await azure_fetcher.fetch_pricing(region)
            
            async with get_db_context() as db:
                for price_info in pricing_data:
                    instance_data = {
                        "provider": "azure",
                        "instance_type": price_info["instance_type"],
                        "vcpus": price_info.get("vcpus", 0),
                        "memory_gb": price_info.get("memory_gb", 0),
                        "network_performance": "Standard",
                        "region": region,
                        "price_per_hour": Decimal(str(price_info["price_per_hour"])),
                        "operating_system": "Linux",
                        "spot_available": price_info.get("spot_available", False),
                        "metadata": {
                            "vm_family": price_info.get("vm_family", "general"),
                        }
                    }
                    
                    stmt = insert(CloudInstance).values(**instance_data)
                    stmt = stmt.on_conflict_do_update(
                        index_elements=["provider", "instance_type", "region"],
                        set_={
                            "price_per_hour": instance_data["price_per_hour"],
                            "updated_at": datetime.utcnow(),
                        }
                    )
                    await db.execute(stmt)
                    stats["azure"]["instances"] += 1
                
                await db.commit()
            
            logger.info(f"✓ Azure {region}: {len(pricing_data)} instances")
        
        print(f"✅ Azure: {stats['azure']['instances']} instances fetched")
        
    except Exception as e:
        error_msg = f"Azure fetch failed: {str(e)}"
        logger.error(error_msg)
        stats["errors"].append(error_msg)
        print(f"❌ Azure failed: {str(e)}")
    
    # ==================== SUMMARY ====================
    end_time = datetime.now()
    stats["total_time"] = (end_time - start_time).total_seconds()
    
    print("\n" + "="*70)
    print("📈 FETCH COMPLETE")
    print("="*70)
    print(f"AWS Instances:   {stats['aws']['instances']}")
    print(f"GCP Instances:   {stats['gcp']['instances']}")
    print(f"Azure Instances: {stats['azure']['instances']}")
    print(f"Total Time:      {stats['total_time']:.1f}s")
    
    if stats["errors"]:
        print(f"\n⚠️  Errors encountered: {len(stats['errors'])}")
        for error in stats["errors"]:
            print(f"  - {error}")
    
    # Count total instances in DB
    async with get_db_context() as db:
        result = await db.execute(select(CloudInstance))
        total_in_db = len(result.all())
        print(f"\n✅ Total instances in database: {total_in_db}")
    
    print("\n🎉 Data fetch complete! Your app now has real pricing data.")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Fetch interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {str(e)}")
        logger.exception("Fatal error during fetch")
        sys.exit(1)
