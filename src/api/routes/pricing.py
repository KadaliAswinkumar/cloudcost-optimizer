"""
Pricing Endpoints
Provides access to EC2 pricing data across different pricing models.
"""

from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models.pricing import OnDemandPricing, SpotPricing
from src.models.cloud_provider import SpotPriceHistory
from src.services.cost_calculator import CostCalculator
from src.services.spot_price_tracker import SpotPriceTracker

router = APIRouter(prefix="/pricing", tags=["Pricing"])


@router.get("/on-demand/{instance_type}")
async def get_on_demand_pricing(
    instance_type: str,
    region: Optional[str] = Query(None, description="Filter by region"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get On-Demand pricing for an instance type.
    
    Args:
        instance_type: EC2 instance type
        region: Optional region filter
        
    Returns:
        On-Demand pricing data
    """
    query = select(OnDemandPricing).where(
        OnDemandPricing.instance_type == instance_type
    )
    
    if region:
        query = query.where(OnDemandPricing.region == region)
    
    query = query.order_by(OnDemandPricing.price_per_hour)
    
    result = await db.execute(query)
    prices = result.scalars().all()
    
    if not prices:
        raise HTTPException(
            status_code=404,
            detail=f"No pricing found for instance type '{instance_type}'"
        )
    
    return {
        "instance_type": instance_type,
        "pricing": [
            {
                "region": p.region,
                "price_per_hour": float(p.price_per_hour),
                "price_per_day": float(p.price_per_hour * 24),
                "price_per_month": float(p.price_per_hour * 730),
                "operating_system": p.operating_system,
                "tenancy": p.tenancy,
            }
            for p in prices
        ],
        "cheapest_region": prices[0].region if prices else None,
    }


@router.get("/spot/{instance_type}")
async def get_spot_pricing(
    instance_type: str,
    region: Optional[str] = Query(None, description="Filter by region"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get current Spot pricing for an instance type.
    
    Args:
        instance_type: EC2 instance type
        region: Optional region filter
        
    Returns:
        Spot pricing data with statistics
    """
    query = select(SpotPricing).where(
        SpotPricing.instance_type == instance_type
    )
    
    if region:
        query = query.where(SpotPricing.region == region)
    
    query = query.order_by(SpotPricing.spot_price)
    
    result = await db.execute(query)
    prices = result.scalars().all()
    
    if not prices:
        raise HTTPException(
            status_code=404,
            detail=f"No spot pricing found for instance type '{instance_type}'"
        )
    
    return {
        "instance_type": instance_type,
        "spot_pricing": [
            {
                "availability_zone": p.availability_zone,
                "region": p.region,
                "current_price": float(p.spot_price),
                "avg_price_24h": float(p.avg_price_24h) if p.avg_price_24h else None,
                "avg_price_7d": float(p.avg_price_7d) if p.avg_price_7d else None,
                "avg_price_30d": float(p.avg_price_30d) if p.avg_price_30d else None,
                "price_volatility": p.price_volatility,
                "interruption_frequency": p.interruption_frequency,
                "last_updated": p.timestamp.isoformat() if p.timestamp else None,
            }
            for p in prices
        ],
        "cheapest_zone": prices[0].availability_zone if prices else None,
        "price_range": {
            "min": float(prices[0].spot_price) if prices else None,
            "max": float(prices[-1].spot_price) if prices else None,
        },
    }


@router.get("/spot/{instance_type}/history")
async def get_spot_price_history(
    instance_type: str,
    availability_zone: str = Query(..., description="Availability zone"),
    days: int = Query(7, le=90, description="Days of history"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get Spot price history for trend analysis.
    
    Args:
        instance_type: EC2 instance type
        availability_zone: Availability zone
        days: Number of days of history
        
    Returns:
        Historical spot prices
    """
    from datetime import datetime, timedelta
    
    since = datetime.utcnow() - timedelta(days=days)
    
    query = select(SpotPriceHistory).where(
        SpotPriceHistory.provider == "aws",
        SpotPriceHistory.instance_type == instance_type,
        SpotPriceHistory.zone == availability_zone,
        SpotPriceHistory.timestamp >= since,
    ).order_by(SpotPriceHistory.timestamp)
    
    result = await db.execute(query)
    history = result.scalars().all()
    
    if not history:
        raise HTTPException(
            status_code=404,
            detail=f"No spot history found for {instance_type} in {availability_zone}"
        )
    
    prices = [float(h.spot_price) for h in history]
    
    return {
        "instance_type": instance_type,
        "availability_zone": availability_zone,
        "period_days": days,
        "data_points": len(history),
        "statistics": {
            "current": prices[-1] if prices else None,
            "average": sum(prices) / len(prices) if prices else None,
            "min": min(prices) if prices else None,
            "max": max(prices) if prices else None,
        },
        "history": [
            {
                "timestamp": h.timestamp.isoformat(),
                "price": float(h.spot_price),
            }
            for h in history
        ],
    }


@router.get("/spot/{instance_type}/risk")
async def get_spot_risk_assessment(
    instance_type: str,
    availability_zone: str = Query(..., description="Availability zone"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get Spot interruption risk assessment.
    
    Args:
        instance_type: EC2 instance type
        availability_zone: Availability zone
        
    Returns:
        Risk assessment with recommendations
    """
    tracker = SpotPriceTracker(db)
    risk_data = await tracker.calculate_interruption_risk(
        instance_type, availability_zone
    )
    
    return {
        "instance_type": instance_type,
        "availability_zone": availability_zone,
        **risk_data,
    }


@router.get("/compare/{instance_type}")
async def compare_pricing_strategies(
    instance_type: str,
    region: str = Query("us-east-1", description="AWS region"),
    hours_per_month: int = Query(730, description="Expected hours per month"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Compare all pricing strategies for an instance type.
    
    Args:
        instance_type: EC2 instance type
        region: AWS region
        hours_per_month: Expected monthly usage hours
        
    Returns:
        Comprehensive pricing comparison
    """
    # Get On-Demand price
    od_query = select(OnDemandPricing).where(
        OnDemandPricing.instance_type == instance_type,
        OnDemandPricing.region == region,
    )
    od_result = await db.execute(od_query)
    on_demand = od_result.scalar_one_or_none()
    
    if not on_demand:
        raise HTTPException(
            status_code=404,
            detail=f"No on-demand pricing found for {instance_type} in {region}"
        )
    
    # Get Spot price
    spot_query = select(SpotPricing).where(
        SpotPricing.instance_type == instance_type,
        SpotPricing.region == region,
    ).order_by(SpotPricing.spot_price).limit(1)
    spot_result = await db.execute(spot_query)
    spot = spot_result.scalar_one_or_none()
    
    # Calculate comparisons
    calculator = CostCalculator()
    comparisons = calculator.compare_all_strategies(
        on_demand.price_per_hour,
        spot.spot_price if spot else None,
    )
    
    # Add monthly projections
    for comp in comparisons:
        comp["monthly_cost"] = comp["effective_hourly"] * hours_per_month
        comp["annual_cost"] = comp["monthly_cost"] * 12
    
    return {
        "instance_type": instance_type,
        "region": region,
        "hours_per_month": hours_per_month,
        "on_demand_hourly": float(on_demand.price_per_hour),
        "spot_available": spot is not None,
        "strategies": comparisons,
        "recommendation": comparisons[0]["strategy"] if comparisons else None,
        "max_savings": comparisons[0]["savings_percentage"] if comparisons else 0,
    }


@router.post("/calculate")
async def calculate_cost(
    instance_type: str = Query(..., description="EC2 instance type"),
    region: str = Query("us-east-1", description="AWS region"),
    count: int = Query(1, ge=1, le=1000, description="Number of instances"),
    hours_per_day: float = Query(24, ge=0, le=24, description="Hours per day"),
    days_per_month: int = Query(30, ge=1, le=31, description="Days per month"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Calculate costs for a specific configuration.
    
    Args:
        instance_type: EC2 instance type
        region: AWS region
        count: Number of instances
        hours_per_day: Daily usage hours
        days_per_month: Monthly usage days
        
    Returns:
        Detailed cost calculation
    """
    # Get On-Demand price
    query = select(OnDemandPricing).where(
        OnDemandPricing.instance_type == instance_type,
        OnDemandPricing.region == region,
    )
    result = await db.execute(query)
    pricing = result.scalar_one_or_none()
    
    if not pricing:
        raise HTTPException(
            status_code=404,
            detail=f"No pricing found for {instance_type} in {region}"
        )
    
    hourly_rate = pricing.price_per_hour
    hours_per_month = hours_per_day * days_per_month
    
    monthly_per_instance = float(hourly_rate) * hours_per_month
    monthly_total = monthly_per_instance * count
    
    return {
        "configuration": {
            "instance_type": instance_type,
            "region": region,
            "count": count,
            "hours_per_day": hours_per_day,
            "days_per_month": days_per_month,
            "hours_per_month": hours_per_month,
        },
        "costs": {
            "hourly_per_instance": float(hourly_rate),
            "daily_per_instance": float(hourly_rate) * hours_per_day,
            "monthly_per_instance": monthly_per_instance,
            "monthly_total": monthly_total,
            "annual_total": monthly_total * 12,
        },
        "currency": "USD",
    }


@router.get("/regions")
async def get_pricing_by_region(
    instance_type: str = Query(..., description="EC2 instance type"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get pricing across all regions for comparison.
    
    Args:
        instance_type: EC2 instance type
        
    Returns:
        Pricing by region sorted by cost
    """
    query = select(OnDemandPricing).where(
        OnDemandPricing.instance_type == instance_type,
    ).order_by(OnDemandPricing.price_per_hour)
    
    result = await db.execute(query)
    prices = result.scalars().all()
    
    if not prices:
        raise HTTPException(
            status_code=404,
            detail=f"No pricing found for instance type '{instance_type}'"
        )
    
    cheapest = prices[0]
    most_expensive = prices[-1]
    
    return {
        "instance_type": instance_type,
        "regions": [
            {
                "region": p.region,
                "hourly_price": float(p.price_per_hour),
                "monthly_price": float(p.price_per_hour * 730),
                "vs_cheapest_pct": round(
                    (float(p.price_per_hour) / float(cheapest.price_per_hour) - 1) * 100, 1
                ),
            }
            for p in prices
        ],
        "summary": {
            "cheapest_region": cheapest.region,
            "cheapest_price": float(cheapest.price_per_hour),
            "most_expensive_region": most_expensive.region,
            "most_expensive_price": float(most_expensive.price_per_hour),
            "price_variance_pct": round(
                (float(most_expensive.price_per_hour) / float(cheapest.price_per_hour) - 1) * 100, 1
            ),
        },
    }

