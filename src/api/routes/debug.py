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
