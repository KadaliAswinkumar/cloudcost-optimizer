#!/usr/bin/env python3
"""
Fetch Real Cloud Pricing Data
Fetches live pricing from AWS, GCP, and Azure APIs
"""

import asyncio
import logging
import sys
from datetime import datetime
from typing import List, Dict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main function to fetch all cloud data."""
    from src.core.database import get_db_context
    from src.models.cloud_provider import CloudInstance, CloudPricing
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
    
    # ==================== GCP ====================
    print("📊 1/3 Fetching GCP Compute Engine Data...")
    print("-" * 70)
    try:
        gcp_fetcher = GCPPriceFetcher()
        
        # Fetch machine types (specs)
        machine_types = await gcp_fetcher.fetch_machine_types()
        
        async with get_db_context() as db:
            for mt in machine_types:
                instance = CloudInstance(
                    provider=mt["provider"],
                    instance_type=mt["instance_type"],
                    instance_family=mt["instance_family"],
                    display_name=mt.get("display_name"),
                    vcpus=mt["vcpus"],
                    memory_gb=mt["memory_gb"],
                    processor_architecture=mt.get("processor_architecture", "x86_64"),
                    cpu_platform=mt.get("cpu_platform"),
                    category=mt.get("category"),
                    is_burstable=mt.get("is_burstable", False),
                    supports_spot=mt.get("supports_spot", True),
                    is_current_generation=mt.get("is_current_generation", True),
                    gpu_count=mt.get("gpu_count"),
                    gpu_type=mt.get("gpu_type"),
                )
                db.add(instance)
                stats["gcp"]["instances"] += 1
            
            await db.commit()
        
        # Fetch pricing for multiple regions (expanded for more coverage)
        gcp_regions = [
            "us-central1", "us-east1", "us-west1", "us-west2",
            "europe-west1", "europe-west2", "europe-west3", "europe-west4",
            "asia-east1", "asia-northeast1", "asia-southeast1"
        ]
        
        for region in gcp_regions:
            pricing_data = await gcp_fetcher.fetch_pricing(region)
            
            async with get_db_context() as db:
                for price in pricing_data:
                    pricing = CloudPricing(
                        provider=price["provider"],
                        instance_type=price["instance_type"],
                        region=price["region"],
                        pricing_type=price["pricing_type"],
                        os_type=price.get("os_type", "linux"),
                        hourly_price=price["hourly_price"],
                        monthly_price=price.get("monthly_price"),
                        commitment_term=price.get("commitment_term"),
                        currency=price.get("currency", "USD"),
                        effective_date=price.get("effective_date", datetime.utcnow()),
                    )
                    db.add(pricing)
                    stats["gcp"]["pricing"] += 1
                
                await db.commit()
        
        logger.info(f"✓ GCP: {stats['gcp']['instances']} instances, {stats['gcp']['pricing']} pricing records")
        print(f"✅ GCP: {stats['gcp']['instances']} instances, {stats['gcp']['pricing']} pricing records")
        
    except Exception as e:
        error_msg = f"GCP fetch failed: {str(e)}"
        logger.error(error_msg)
        stats["errors"].append(error_msg)
        print(f"❌ GCP failed: {str(e)}")
    
    # ==================== AZURE ====================
    print("\n📊 2/3 Fetching Azure Virtual Machines Data...")
    print("-" * 70)
    try:
        azure_fetcher = AzurePriceFetcher()
        
        # Fetch VM sizes (specs)
        vm_sizes = await azure_fetcher.fetch_vm_sizes()
        
        async with get_db_context() as db:
            for vm in vm_sizes:
                instance = CloudInstance(
                    provider=vm["provider"],
                    instance_type=vm["instance_type"],
                    instance_family=vm["instance_family"],
                    display_name=vm.get("display_name"),
                    vcpus=vm["vcpus"],
                    memory_gb=vm["memory_gb"],
                    processor_architecture=vm.get("processor_architecture", "x86_64"),
                    local_ssd_gb=vm.get("local_ssd_gb"),
                    storage_type=vm.get("storage_type", "Premium SSD"),
                    category=vm.get("category"),
                    is_burstable=vm.get("is_burstable", False),
                    supports_spot=vm.get("supports_spot", True),
                    is_current_generation=vm.get("is_current_generation", True),
                    gpu_count=vm.get("gpu_count"),
                    gpu_type=vm.get("gpu_type"),
                )
                db.add(instance)
                stats["azure"]["instances"] += 1
            
            await db.commit()
        
        # Fetch pricing for multiple regions (expanded for more coverage)
        azure_regions = [
            "eastus", "eastus2", "westus", "westus2", "westus3",
            "northeurope", "westeurope", "uksouth",
            "southeastasia", "australiaeast", "japaneast"
        ]
        
        for region in azure_regions:
            pricing_data = await azure_fetcher.fetch_pricing(region)
            
            async with get_db_context() as db:
                for price in pricing_data:
                    pricing = CloudPricing(
                        provider=price["provider"],
                        instance_type=price["instance_type"],
                        region=price["region"],
                        pricing_type=price["pricing_type"],
                        os_type=price.get("os_type", "linux"),
                        hourly_price=price["hourly_price"],
                        monthly_price=price.get("monthly_price"),
                        commitment_term=price.get("commitment_term"),
                        currency=price.get("currency", "USD"),
                        effective_date=price.get("effective_date", datetime.utcnow()),
                    )
                    db.add(pricing)
                    stats["azure"]["pricing"] += 1
                
                await db.commit()
        
        logger.info(f"✓ Azure: {stats['azure']['instances']} instances, {stats['azure']['pricing']} pricing records")
        print(f"✅ Azure: {stats['azure']['instances']} instances, {stats['azure']['pricing']} pricing records")
        
    except Exception as e:
        error_msg = f"Azure fetch failed: {str(e)}"
        logger.error(error_msg)
        stats["errors"].append(error_msg)
        print(f"❌ Azure failed: {str(e)}")
    
    # ==================== AWS ====================
    print("\n📊 3/3 Fetching AWS EC2 Data...")
    print("-" * 70)
    try:
        aws_fetcher = AWSPriceFetcher()
        
        # Fetch instance types (specs)
        instance_types = await aws_fetcher.fetch_instance_types()
        
        async with get_db_context() as db:
            for it in instance_types:
                instance = CloudInstance(
                    provider="aws",
                    instance_type=it["instance_type"],
                    instance_family=it["instance_family"],
                    display_name=it.get("instance_type"),
                    vcpus=it["vcpus"],
                    memory_gb=it["memory_gb"],
                    processor_architecture=it.get("processor_architecture", "x86_64"),
                    storage_type=it.get("storage_type"),
                    category="general_purpose",
                    is_current_generation=it.get("current_generation", True),
                    supports_spot=True,
                )
                db.add(instance)
                stats["aws"]["instances"] += 1
            
            await db.commit()
        
        # Fetch pricing for multiple regions
        aws_regions = ["us-east-1", "us-west-2", "eu-west-1"]
        
        for region in aws_regions:
            # Fetch on-demand pricing
            pricing_data = await aws_fetcher.fetch_on_demand_pricing(region)
            
            async with get_db_context() as db:
                for price in pricing_data:
                    pricing = CloudPricing(
                        provider="aws",
                        instance_type=price["instance_type"],
                        region=price["region"],
                        pricing_type="on_demand",
                        os_type=price.get("operating_system", "Linux").lower(),
                        hourly_price=price["price_per_hour"],
                        monthly_price=price["price_per_hour"] * 730,
                        currency="USD",
                        effective_date=price.get("effective_date", datetime.utcnow()),
                    )
                    db.add(pricing)
                    stats["aws"]["pricing"] += 1
                
                await db.commit()
        
        logger.info(f"✓ AWS: {stats['aws']['instances']} instances, {stats['aws']['pricing']} pricing records")
        print(f"✅ AWS: {stats['aws']['instances']} instances, {stats['aws']['pricing']} pricing records")
        
    except Exception as e:
        error_msg = f"AWS fetch failed: {str(e)}"
        logger.error(error_msg)
        stats["errors"].append(error_msg)
        print(f"❌ AWS failed: {str(e)}")
    
    # ==================== SUMMARY ====================
    end_time = datetime.now()
    stats["total_time"] = (end_time - start_time).total_seconds()
    
    print("\n" + "="*70)
    print("📈 FETCH COMPLETE")
    print("="*70)
    print(f"GCP:   {stats['gcp']['instances']} instances, {stats['gcp']['pricing']} pricing records")
    print(f"Azure: {stats['azure']['instances']} instances, {stats['azure']['pricing']} pricing records")
    print(f"AWS:   {stats['aws']['instances']} instances, {stats['aws']['pricing']} pricing records")
    print(f"Total Time: {stats['total_time']:.1f}s")
    
    if stats["errors"]:
        print(f"\n⚠️  Errors encountered: {len(stats['errors'])}")
        for error in stats["errors"]:
            print(f"  - {error}")
    
    # Count total instances in DB
    from sqlalchemy import select, func
    async with get_db_context() as db:
        result = await db.execute(select(func.count()).select_from(CloudInstance))
        total_instances = result.scalar()
        result = await db.execute(select(func.count()).select_from(CloudPricing))
        total_pricing = result.scalar()
        print(f"\n✅ Total in database: {total_instances} instances, {total_pricing} pricing records")
    
    print("\n🎉 Data fetch complete!")
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
