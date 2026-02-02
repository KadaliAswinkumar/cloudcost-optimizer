#!/usr/bin/env python3
"""
Fetch Real Cloud Pricing Data
Fetches live pricing from AWS, GCP, and Azure APIs
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Add project root to path so we can import src modules
# This handles the case where script is run from /opt/render/project/src
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

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
    from asyncpg.exceptions import UniqueViolationError
    from sqlalchemy.exc import IntegrityError
    
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
        
        # Clear existing GCP instances to avoid duplicates (fresh start)
        async with get_db_context() as db:
            from sqlalchemy import delete
            await db.execute(delete(CloudInstance).where(CloudInstance.provider == "gcp"))
            await db.commit()
            logger.info("Cleared existing GCP instances")
        
        # Now insert all new GCP instances
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
            logger.info(f"✓ Inserted {stats['gcp']['instances']} GCP instances")
        
        # Clear existing GCP pricing to avoid duplicates
        async with get_db_context() as db:
            from sqlalchemy import delete
            await db.execute(delete(CloudPricing).where(CloudPricing.provider == "gcp"))
            await db.commit()
            logger.info("Cleared existing GCP pricing")
        
        # Fetch pricing for multiple regions (expanded for MORE coverage)
        gcp_regions = [
            # US regions
            "us-central1", "us-east1", "us-east4", "us-west1", "us-west2", "us-west3", "us-west4",
            # Europe regions
            "europe-west1", "europe-west2", "europe-west3", "europe-west4", "europe-west6",
            "europe-north1", "europe-central2",
            # Asia regions
            "asia-east1", "asia-east2", "asia-northeast1", "asia-northeast2", "asia-northeast3",
            "asia-south1", "asia-south2", "asia-southeast1", "asia-southeast2",
            # Other regions
            "australia-southeast1", "southamerica-east1", "northamerica-northeast1"
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
        
        # Clear existing Azure instances to avoid duplicates (fresh start)
        async with get_db_context() as db:
            from sqlalchemy import delete
            await db.execute(delete(CloudInstance).where(CloudInstance.provider == "azure"))
            await db.commit()
            logger.info("Cleared existing Azure instances")
        
        # Now insert all new Azure instances
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
            logger.info(f"✓ Inserted {stats['azure']['instances']} Azure instances")
        
        # Clear existing Azure pricing to avoid duplicates
        async with get_db_context() as db:
            from sqlalchemy import delete
            await db.execute(delete(CloudPricing).where(CloudPricing.provider == "azure"))
            await db.commit()
            logger.info("Cleared existing Azure pricing")
        
        # Fetch pricing for multiple regions (expanded for MORE coverage)
        azure_regions = [
            # US regions
            "eastus", "eastus2", "centralus", "northcentralus", "southcentralus",
            "westus", "westus2", "westus3", "westcentralus",
            # Europe regions
            "northeurope", "westeurope", "francecentral", "germanywestcentral",
            "norwayeast", "switzerlandnorth", "uksouth", "ukwest",
            # Asia regions
            "eastasia", "southeastasia", "japaneast", "japanwest", "koreacentral",
            "southindia", "centralindia", "westindia",
            # Other regions  
            "australiaeast", "australiasoutheast", "brazilsouth", "canadacentral", "canadaeast"
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
    
    aws_fetcher = AWSPriceFetcher()
    
    # Fetch instance types (specs) - wrapped in own try-except
    try:
        instance_types = await aws_fetcher.fetch_instance_types()
        
        async with get_db_context() as db:
            for it in instance_types:
                try:
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
                    await db.merge(instance)  # merge instead of add - updates if exists, inserts if not
                    stats["aws"]["instances"] += 1
                except (IntegrityError, UniqueViolationError):
                    # Silently skip duplicates
                    await db.rollback()
                except Exception as inst_err:
                    # Skip this instance and continue
                    logger.warning(f"Skipping AWS instance {it.get('instance_type')}: {inst_err}")
                    await db.rollback()
            
            try:
                await db.commit()
            except (IntegrityError, UniqueViolationError):
                # Ignore duplicate errors on commit
                await db.rollback()
        
        logger.info(f"✓ AWS instances: {stats['aws']['instances']}")
        print(f"✅ AWS instances: {stats['aws']['instances']}")
    except Exception as e:
        logger.error(f"AWS instance fetch error: {e}")
        print(f"⚠️  AWS instance fetch had errors (continuing to pricing...)")
    
    # Fetch pricing for multiple regions - ALWAYS TRY even if instances failed
    aws_regions = ["us-east-1", "us-west-2", "eu-west-1", "ap-south-1", "eu-central-1"]
    
    # Clear existing AWS pricing to avoid duplicates
    async with get_db_context() as db:
        from sqlalchemy import delete
        await db.execute(delete(CloudPricing).where(CloudPricing.provider == "aws"))
        await db.commit()
        logger.info("Cleared existing AWS pricing")
    
    for region in aws_regions:
        try:
            # Fetch on-demand pricing
            pricing_data = await aws_fetcher.fetch_on_demand_pricing(region)
            
            async with get_db_context() as db:
                for price in pricing_data:
                    try:
                        pricing = CloudPricing(
                            provider="aws",
                            instance_type=price["instance_type"],
                            region=price["region"],
                            pricing_type="on_demand",
                            os_type=price.get("operating_system", "Linux").lower(),
                            hourly_price=float(price["price_per_hour"]),
                            monthly_price=float(price["price_per_hour"]) * 730,
                            currency="USD",
                            effective_date=price.get("effective_date", datetime.utcnow()),
                        )
                        db.add(pricing)
                        stats["aws"]["pricing"] += 1
                    except (IntegrityError, UniqueViolationError):
                        # Silently skip duplicates
                        await db.rollback()
                    except Exception as price_err:
                        # Skip this price and continue
                        logger.warning(f"Skipping AWS price for {price.get('instance_type')}: {price_err}")
                        await db.rollback()
                
                try:
                    await db.commit()
                except (IntegrityError, UniqueViolationError):
                    # Ignore duplicate errors on commit
                    await db.rollback()
            
            logger.info(f"✓ AWS {region}: fetched {len(pricing_data)} prices")
        except Exception as region_err:
            logger.error(f"AWS pricing fetch failed for {region}: {region_err}")
            stats["errors"].append(f"AWS {region}: {region_err}")
            # Continue to next region
    
    logger.info(f"✓ AWS TOTAL: {stats['aws']['instances']} instances, {stats['aws']['pricing']} pricing records")
    print(f"✅ AWS TOTAL: {stats['aws']['instances']} instances, {stats['aws']['pricing']} pricing records")
    
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
        print(f"\n\n⚠️  Fetch had errors but may have loaded some data: {str(e)}")
        logger.exception("Error during fetch (non-fatal)")
        # Don't exit with error code - let the app start anyway
        sys.exit(0)
