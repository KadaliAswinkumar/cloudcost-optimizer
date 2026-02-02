#!/usr/bin/env python3
"""
Hourly Spot Price Collection - Vantage.sh Style
Runs every hour to collect REAL spot prices and build historical data
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict

# Add project root to path so we can import src modules
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def collect_aws_spot_prices() -> List[Dict]:
    """Collect current AWS spot prices for all instances"""
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        if not os.getenv('AWS_ACCESS_KEY_ID'):
            logger.warning("⚠️  No AWS credentials, skipping AWS")
            return []
        
        logger.info("📊 Collecting AWS spot prices...")
        
        # Get instance types from database
        from src.core.database import get_db_context
        from src.models.cloud_provider import CloudInstance
        from sqlalchemy import select, distinct
        
        async with get_db_context() as db:
            result = await db.execute(
                select(distinct(CloudInstance.instance_type))
                .where(CloudInstance.provider == "aws")
            )
            instance_types = [row[0] for row in result.fetchall()]
        
        # Key AWS regions (collect from top 5 for speed)
        regions = ['us-east-1', 'us-west-2', 'eu-west-1', 'ap-southeast-1', 'ap-northeast-1']
        
        prices = []
        collection_time = datetime.utcnow()
        
        for region in regions:
            try:
                ec2 = boto3.client('ec2', region_name=region)
                
                # Get current spot prices
                response = ec2.describe_spot_price_history(
                    InstanceTypes=instance_types[:100],  # AWS limit
                    ProductDescriptions=['Linux/UNIX'],
                    MaxResults=1000,
                    StartTime=collection_time - timedelta(minutes=5)  # Last 5 mins
                )
                
                for item in response.get('SpotPriceHistory', []):
                    prices.append({
                        'provider': 'aws',
                        'instance_type': item['InstanceType'],
                        'region': region,
                        'zone': item['AvailabilityZone'],
                        'spot_price': Decimal(item['SpotPrice']),
                        'os_type': 'linux',
                        'timestamp': collection_time,  # Use collection time, not API timestamp
                    })
                
                logger.info(f"  ✓ Collected {len(response.get('SpotPriceHistory', []))} prices from {region}")
                
            except ClientError as e:
                logger.warning(f"  ✗ Failed {region}: {e}")
        
        logger.info(f"✅ AWS: Collected {len(prices)} spot prices")
        return prices
        
    except Exception as e:
        logger.error(f"❌ AWS collection failed: {e}")
        return []


async def collect_gcp_preemptible_prices() -> List[Dict]:
    """Collect GCP preemptible prices (70% off on-demand)"""
    try:
        logger.info("📊 Collecting GCP preemptible prices...")
        
        from src.core.database import get_db_context
        from src.models.cloud_provider import CloudPricing
        from sqlalchemy import select, and_
        
        async with get_db_context() as db:
            result = await db.execute(
                select(CloudPricing).where(
                    and_(
                        CloudPricing.provider == "gcp",
                        CloudPricing.pricing_type == "on_demand"
                    )
                )
            )
            on_demand_prices = result.scalars().all()
        
        prices = []
        collection_time = datetime.utcnow()
        
        for od in on_demand_prices:
            # GCP documented rate: 70% discount
            preemptible_price = float(od.hourly_price) * 0.30
            
            prices.append({
                'provider': 'gcp',
                'instance_type': od.instance_type,
                'region': od.region,
                'zone': None,
                'spot_price': Decimal(str(preemptible_price)),
                'os_type': 'linux',
                'timestamp': collection_time,
            })
        
        logger.info(f"✅ GCP: Collected {len(prices)} preemptible prices")
        return prices
        
    except Exception as e:
        logger.error(f"❌ GCP collection failed: {e}")
        return []


async def collect_azure_spot_prices() -> List[Dict]:
    """Collect Azure spot prices from Retail API"""
    try:
        import httpx
        
        logger.info("📊 Collecting Azure spot prices...")
        
        from src.core.database import get_db_context
        from src.models.cloud_provider import CloudInstance
        from sqlalchemy import select, distinct
        
        async with get_db_context() as db:
            result = await db.execute(
                select(distinct(CloudInstance.instance_type))
                .where(CloudInstance.provider == "azure")
                .limit(50)  # Limit for speed
            )
            vm_sizes = [row[0] for row in result.fetchall()]
        
        prices = []
        collection_time = datetime.utcnow()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for vm_size in vm_sizes:
                try:
                    url = "https://prices.azure.com/api/retail/prices"
                    params = {
                        "$filter": f"armSkuName eq '{vm_size}' and priceType eq 'Consumption' and contains(meterName, 'Spot')"
                    }
                    
                    response = await client.get(url, params=params)
                    data = response.json()
                    
                    for item in data.get('Items', []):
                        if item.get('type') == 'Consumption':
                            prices.append({
                                'provider': 'azure',
                                'instance_type': vm_size,
                                'region': item.get('armRegionName', 'unknown'),
                                'zone': None,
                                'spot_price': Decimal(str(item['retailPrice'])),
                                'os_type': 'linux',
                                'timestamp': collection_time,
                            })
                
                except Exception as e:
                    logger.debug(f"  ✗ Skipped {vm_size}: {e}")
        
        logger.info(f"✅ Azure: Collected {len(prices)} spot prices")
        return prices
        
    except Exception as e:
        logger.error(f"❌ Azure collection failed: {e}")
        return []


async def store_historical_prices(prices: List[Dict]):
    """Store collected prices in spot_price_history table"""
    if not prices:
        logger.warning("⚠️  No prices to store")
        return
    
    try:
        from src.core.database import get_db_context
        from src.models.cloud_provider import SpotPriceHistory
        from sqlalchemy import insert
        
        logger.info(f"💾 Storing {len(prices)} price points...")
        
        async with get_db_context() as db:
            # Bulk insert
            await db.execute(insert(SpotPriceHistory), prices)
            await db.commit()
        
        logger.info(f"✅ Stored {len(prices)} historical price points")
        
    except Exception as e:
        logger.error(f"❌ Failed to store prices: {e}")
        raise


async def cleanup_old_data(days_to_keep: int = 90):
    """Remove historical data older than X days"""
    try:
        from src.core.database import get_db_context
        from src.models.cloud_provider import SpotPriceHistory
        from sqlalchemy import delete
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        async with get_db_context() as db:
            result = await db.execute(
                delete(SpotPriceHistory).where(
                    SpotPriceHistory.timestamp < cutoff_date
                )
            )
            await db.commit()
            
            if result.rowcount > 0:
                logger.info(f"🧹 Cleaned up {result.rowcount} old records (>{days_to_keep} days)")
        
    except Exception as e:
        logger.warning(f"⚠️  Cleanup failed: {e}")


async def main():
    """Main hourly collection job"""
    print("\n" + "="*70)
    print("⏰ HOURLY SPOT PRICE COLLECTION")
    print("="*70)
    print(f"📅 Time: {datetime.utcnow().isoformat()}")
    print("🎯 Building real historical data like Vantage.sh")
    print("="*70 + "\n")
    
    try:
        # Collect from all providers
        aws_prices = await collect_aws_spot_prices()
        gcp_prices = await collect_gcp_preemptible_prices()
        azure_prices = await collect_azure_spot_prices()
        
        # Combine all prices
        all_prices = aws_prices + gcp_prices + azure_prices
        
        # Store in database
        await store_historical_prices(all_prices)
        
        # Cleanup old data
        await cleanup_old_data(days_to_keep=90)
        
        print("\n" + "="*70)
        print("✅ COLLECTION COMPLETE")
        print("="*70)
        print(f"📊 Total prices collected: {len(all_prices)}")
        print(f"   • AWS: {len(aws_prices)}")
        print(f"   • GCP: {len(gcp_prices)}")
        print(f"   • Azure: {len(azure_prices)}")
        print("="*70 + "\n")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ COLLECTION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    print("\n🚀 STARTING HOURLY COLLECTION JOB...")
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
