"""
Debug endpoints to check database status
Temporary endpoints to diagnose data loading issues
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from src.core.database import get_db
from src.models.cloud_provider import CloudInstance, CloudPricing, SpotPriceHistory

router = APIRouter(prefix="/debug", tags=["Debug"])


@router.get("/database-status", response_model=Dict[str, Any])
async def get_database_status(db: AsyncSession = Depends(get_db)):
    """
    Check what data is actually in the database
    """
    try:
        # Count instances
        instances_result = await db.execute(
            select(func.count()).select_from(CloudInstance)
        )
        total_instances = instances_result.scalar()
        
        # Count instances by provider
        aws_instances = await db.execute(
            select(func.count()).select_from(CloudInstance)
            .where(CloudInstance.provider == "aws")
        )
        gcp_instances = await db.execute(
            select(func.count()).select_from(CloudInstance)
            .where(CloudInstance.provider == "gcp")
        )
        azure_instances = await db.execute(
            select(func.count()).select_from(CloudInstance)
            .where(CloudInstance.provider == "azure")
        )
        
        # Count pricing records
        all_pricing = await db.execute(
            select(func.count()).select_from(CloudPricing)
        )
        
        on_demand_pricing = await db.execute(
            select(func.count()).select_from(CloudPricing)
            .where(CloudPricing.pricing_type == "on_demand")
        )
        
        spot_pricing = await db.execute(
            select(func.count()).select_from(CloudPricing)
            .where(CloudPricing.pricing_type.in_(["spot", "preemptible"]))
        )
        
        reserved_pricing = await db.execute(
            select(func.count()).select_from(CloudPricing)
            .where(CloudPricing.pricing_type.in_(["reserved_1yr", "reserved_3yr", "committed_1yr", "committed_3yr"]))
        )
        
        # Count historical spot prices
        spot_history = await db.execute(
            select(func.count()).select_from(SpotPriceHistory)
        )
        
        # Get sample on-demand pricing (limit 3 to avoid issues)
        sample_pricing_result = await db.execute(
            select(CloudPricing)
            .where(CloudPricing.pricing_type == "on_demand")
            .limit(3)
        )
        sample_pricing = sample_pricing_result.scalars().all()
        
        # Get sample spot pricing
        sample_spot_result = await db.execute(
            select(CloudPricing)
            .where(CloudPricing.pricing_type.in_(["spot", "preemptible"]))
            .limit(3)
        )
        sample_spot = sample_spot_result.scalars().all()
        
        return {
            "instances": {
                "total": total_instances,
                "aws": aws_instances.scalar(),
                "gcp": gcp_instances.scalar(),
                "azure": azure_instances.scalar()
            },
            "pricing": {
                "total": all_pricing.scalar(),
                "on_demand": on_demand_pricing.scalar(),
                "spot": spot_pricing.scalar(),
                "reserved": reserved_pricing.scalar()
            },
            "spot_history": {
                "total": spot_history.scalar()
            },
            "sample_on_demand_pricing": [
                {
                    "provider": p.provider,
                    "instance_type": p.instance_type,
                    "region": p.region,
                    "zone": p.zone,
                    "hourly_price": float(p.hourly_price),
                    "pricing_type": p.pricing_type
                }
                for p in sample_pricing
            ],
            "sample_spot_pricing": [
                {
                    "provider": p.provider,
                    "instance_type": p.instance_type,
                    "region": p.region,
                    "zone": p.zone,
                    "hourly_price": float(p.hourly_price),
                    "pricing_type": p.pricing_type
                }
                for p in sample_spot
            ],
            "diagnosis": {
                "instances_loaded": total_instances > 0,
                "on_demand_pricing_loaded": on_demand_pricing.scalar() > 0,
                "spot_pricing_loaded": spot_pricing.scalar() > 0,
                "spot_history_collected": spot_history.scalar() > 0,
                "issues": []
            }
        }
    
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc(),
            "message": "Failed to fetch database status"
        }


@router.get("/pricing-for-instance/{provider}/{instance_type}")
async def get_pricing_for_instance(
    provider: str,
    instance_type: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Check what pricing exists for a specific instance
    """
    try:
        # Get all pricing for this instance
        pricing_result = await db.execute(
            select(CloudPricing)
            .where(
                CloudPricing.provider == provider,
                CloudPricing.instance_type == instance_type
            )
        )
        pricing_records = pricing_result.scalars().all()
        
        return {
            "provider": provider,
            "instance_type": instance_type,
            "pricing_records_found": len(pricing_records),
            "pricing": [
                {
                    "region": p.region,
                    "zone": p.zone,
                    "pricing_type": p.pricing_type,
                    "hourly_price": float(p.hourly_price),
                    "monthly_price": float(p.monthly_price)
                }
                for p in pricing_records
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch pricing: {str(e)}")


@router.post("/trigger-spot-pricing")
async def trigger_spot_pricing_fetch(db: AsyncSession = Depends(get_db)):
    """
    🚀 DIAGNOSTIC ENDPOINT: Manually trigger spot pricing fetch
    
    This endpoint runs the spot pricing collection logic and returns detailed output.
    Use this to diagnose why spot pricing isn't loading during deployment.
    
    **What it does:**
    1. Fetches real AWS spot prices (if credentials available)
    2. Calculates GCP preemptible prices (70% off on-demand)
    3. Fetches Azure spot prices from Retail API
    4. Inserts all into cloud_pricing table using UPSERT
    5. Returns detailed logs and statistics
    
    **Returns:**
    - Success/failure status
    - Number of prices collected per provider
    - Any errors encountered
    - Verification of data insertion
    
    **Warning:** This endpoint is for debugging only. It may take 30-60 seconds to complete.
    """
    import logging
    from io import StringIO
    from decimal import Decimal
    from datetime import datetime
    import os
    
    # Capture logs
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    
    logger = logging.getLogger('spot_pricing_debug')
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    
    results = {
        "started_at": datetime.utcnow().isoformat(),
        "aws": {"status": "pending", "count": 0, "error": None},
        "gcp": {"status": "pending", "count": 0, "error": None},
        "azure": {"status": "pending", "count": 0, "error": None},
        "insertion": {"status": "pending", "count": 0, "error": None},
        "logs": [],
        "environment": {
            "aws_credentials_set": bool(os.getenv('AWS_ACCESS_KEY_ID')),
            "database_connected": True
        }
    }
    
    try:
        # 1. Check AWS credentials
        logger.info("Checking AWS credentials...")
        if not os.getenv('AWS_ACCESS_KEY_ID') or not os.getenv('AWS_SECRET_ACCESS_KEY'):
            logger.warning("⚠️  AWS credentials not set - will skip real AWS prices")
            results["aws"]["status"] = "skipped"
            results["aws"]["error"] = "Credentials not configured"
        
        # 2. Check on-demand pricing exists (needed for GCP/Azure)
        logger.info("Checking on-demand pricing data...")
        on_demand_count = await db.execute(
            select(func.count()).select_from(CloudPricing).where(
                CloudPricing.pricing_type == "on_demand"
            )
        )
        on_demand_total = on_demand_count.scalar()
        logger.info(f"Found {on_demand_total} on-demand prices in database")
        
        if on_demand_total == 0:
            logger.error("❌ No on-demand pricing found! fetch_real_data.py must run first.")
            results["insertion"]["status"] = "failed"
            results["insertion"]["error"] = "No on-demand pricing exists (prerequisite)"
            results["logs"] = log_stream.getvalue().split('\n')
            return results
        
        # 3. Fetch AWS spot prices (simplified version)
        all_spot_prices = []
        
        if os.getenv('AWS_ACCESS_KEY_ID'):
            try:
                import boto3
                from botocore.exceptions import ClientError
                
                logger.info("Fetching AWS spot prices...")
                ec2 = boto3.client('ec2', region_name='us-east-1')
                
                # Get a few instance types for testing
                test_instances = ['t3.micro', 't3.small', 't3.medium', 'm5.large', 'c5.large']
                
                response = ec2.describe_spot_price_history(
                    InstanceTypes=test_instances,
                    ProductDescriptions=['Linux/UNIX'],
                    MaxResults=50
                )
                
                for item in response.get('SpotPriceHistory', []):
                    timestamp = item['Timestamp']
                    if timestamp.tzinfo is not None:
                        timestamp = timestamp.replace(tzinfo=None)
                    
                    all_spot_prices.append({
                        'provider': 'aws',
                        'instance_type': item['InstanceType'],
                        'region': 'us-east-1',
                        'zone': item['AvailabilityZone'],
                        'pricing_type': 'spot',
                        'os_type': 'linux',
                        'hourly_price': Decimal(item['SpotPrice']),
                        'monthly_price': Decimal(item['SpotPrice']) * 730,
                        'currency': 'USD',
                        'effective_date': timestamp,
                        'created_at': datetime.utcnow(),
                        'updated_at': datetime.utcnow()
                    })
                
                results["aws"]["status"] = "success"
                results["aws"]["count"] = len(all_spot_prices)
                logger.info(f"✅ Fetched {len(all_spot_prices)} AWS spot prices")
                
            except Exception as e:
                logger.error(f"AWS fetch failed: {e}")
                results["aws"]["status"] = "failed"
                results["aws"]["error"] = str(e)
        
        # 4. Fetch GCP preemptible (70% off on-demand)
        try:
            logger.info("Calculating GCP preemptible prices...")
            gcp_od = await db.execute(
                select(CloudPricing).where(
                    CloudPricing.provider == "gcp",
                    CloudPricing.pricing_type == "on_demand"
                ).limit(10)  # Just 10 for testing
            )
            gcp_prices = gcp_od.scalars().all()
            
            PREEMPTIBLE_DISCOUNT = Decimal('0.30')
            gcp_count = 0
            
            for od_price in gcp_prices:
                preemptible_hourly = od_price.hourly_price * PREEMPTIBLE_DISCOUNT
                
                all_spot_prices.append({
                    'provider': 'gcp',
                    'instance_type': od_price.instance_type,
                    'region': od_price.region,
                    'zone': od_price.zone,
                    'pricing_type': 'preemptible',
                    'os_type': od_price.os_type,
                    'hourly_price': preemptible_hourly,
                    'monthly_price': preemptible_hourly * 730,
                    'currency': 'USD',
                    'effective_date': datetime.utcnow(),
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                })
                gcp_count += 1
            
            results["gcp"]["status"] = "success"
            results["gcp"]["count"] = gcp_count
            logger.info(f"✅ Generated {gcp_count} GCP preemptible prices")
            
        except Exception as e:
            logger.error(f"GCP calculation failed: {e}")
            results["gcp"]["status"] = "failed"
            results["gcp"]["error"] = str(e)
        
        # 5. Insert spot prices using UPSERT
        if all_spot_prices:
            try:
                logger.info(f"Inserting {len(all_spot_prices)} spot prices...")
                
                from sqlalchemy.dialects.postgresql import insert
                
                stmt = insert(CloudPricing).values(all_spot_prices)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['provider', 'instance_type', 'region', 'zone', 'pricing_type', 'os_type'],
                    set_={
                        'hourly_price': stmt.excluded.hourly_price,
                        'monthly_price': stmt.excluded.monthly_price,
                        'updated_at': stmt.excluded.updated_at,
                    }
                )
                
                await db.execute(stmt)
                await db.commit()
                
                # Verify insertion
                verify_result = await db.execute(
                    select(func.count()).select_from(CloudPricing).where(
                        CloudPricing.pricing_type.in_(['spot', 'preemptible'])
                    )
                )
                total_spot = verify_result.scalar()
                
                results["insertion"]["status"] = "success"
                results["insertion"]["count"] = len(all_spot_prices)
                results["insertion"]["total_spot_in_db"] = total_spot
                logger.info(f"✅ Successfully inserted {len(all_spot_prices)} prices")
                logger.info(f"✅ Total spot prices in database: {total_spot}")
                
            except Exception as e:
                logger.error(f"Insertion failed: {e}")
                results["insertion"]["status"] = "failed"
                results["insertion"]["error"] = str(e)
                import traceback
                results["insertion"]["traceback"] = traceback.format_exc()
        else:
            logger.warning("No spot prices to insert")
            results["insertion"]["status"] = "skipped"
            results["insertion"]["error"] = "No prices collected"
        
        results["logs"] = log_stream.getvalue().split('\n')
        results["completed_at"] = datetime.utcnow().isoformat()
        
        return results
        
    except Exception as e:
        results["logs"] = log_stream.getvalue().split('\n')
        results["fatal_error"] = str(e)
        import traceback
        results["traceback"] = traceback.format_exc()
        return results
