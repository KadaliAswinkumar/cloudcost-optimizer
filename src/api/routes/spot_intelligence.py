"""
Spot Intelligence™ API Routes
Real-time spot pricing analysis and interruption prediction
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.services.spot_intelligence import SpotIntelligence

router = APIRouter(prefix="/spot-intelligence", tags=["Spot Intelligence™"])


class SpotAnalysisRequest(BaseModel):
    """Request model for spot analysis"""
    provider: str = Field(..., description="Cloud provider (aws, gcp, azure)")
    instance_type: str = Field(..., description="Instance type (e.g., m5.xlarge)")
    region: Optional[str] = Field(None, description="Specific region (optional)")
    hours_per_month: int = Field(730, ge=1, le=730, description="Usage hours per month")


class ProviderComparisonRequest(BaseModel):
    """Request model for cross-provider comparison"""
    vcpus: int = Field(..., ge=1, le=256, description="Number of vCPUs")
    memory_gb: float = Field(..., ge=0.5, le=4096, description="Memory in GB")
    hours_per_month: int = Field(730, ge=1, le=730, description="Usage hours per month")


@router.post("/analyze")
async def analyze_spot_instance(
    request: SpotAnalysisRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze spot instance pricing and interruption risk
    
    **Spot Intelligence™** provides:
    - 💰 Real-time spot vs on-demand pricing comparison
    - ⚠️ Interruption risk prediction (low/medium/high)
    - 📊 Price volatility analysis
    - 🌍 Best regions for spot instances
    - 💡 Monthly/annual savings calculations
    
    This helps you:
    - Save 70-90% with spot instances
    - Minimize interruption risk
    - Choose optimal regions
    - Make data-driven decisions
    
    Example:
    ```json
    {
      "provider": "aws",
      "instance_type": "m5.xlarge",
      "region": "us-east-1",
      "hours_per_month": 730
    }
    ```
    
    Returns complete analysis with:
    - On-demand pricing
    - Average/min/max spot prices
    - Volatility and risk scores
    - Potential savings
    - Best regions
    """
    try:
        intel = SpotIntelligence(db)
        
        analysis = await intel.analyze_instance(
            provider=request.provider,
            instance_type=request.instance_type,
            region=request.region,
            hours_per_month=request.hours_per_month
        )
        
        if not analysis.get("success"):
            raise HTTPException(status_code=404, detail=analysis.get("error", "Analysis failed"))
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze spot instance: {str(e)}"
        )


@router.post("/compare")
async def compare_spot_across_providers(
    request: ProviderComparisonRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Compare spot pricing across AWS, GCP, and Azure
    
    Find the CHEAPEST spot instances across all clouds for your specs.
    
    **What you get:**
    - Top 10 cheapest options across all providers
    - Sorted by savings (highest first)
    - Complete risk analysis for each
    - Best regions per provider
    
    Perfect for:
    - Multi-cloud cost comparison
    - Finding the absolute cheapest option
    - Validating current cloud choice
    
    Example:
    ```json
    {
      "vcpus": 4,
      "memory_gb": 16,
      "hours_per_month": 730
    }
    ```
    """
    try:
        intel = SpotIntelligence(db)
        
        comparison = await intel.compare_providers(
            instance_specs={
                "vcpus": request.vcpus,
                "memory_gb": request.memory_gb
            },
            hours_per_month=request.hours_per_month
        )
        
        if not comparison.get("success"):
            raise HTTPException(status_code=404, detail=comparison.get("error", "Comparison failed"))
        
        return comparison
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compare providers: {str(e)}"
        )


@router.get("/quick-check")
async def quick_spot_check(
    provider: str = Query(..., description="Cloud provider"),
    instance_type: str = Query(..., description="Instance type"),
    db: AsyncSession = Depends(get_db)
):
    """
    Quick spot price check (simplified response)
    
    Fast endpoint for getting just the key metrics:
    - Current spot vs on-demand price
    - Savings percentage
    - Risk level
    
    Perfect for dashboards and quick lookups.
    
    Example:
    `/api/v1/spot-intelligence/quick-check?provider=aws&instance_type=m5.xlarge`
    """
    try:
        intel = SpotIntelligence(db)
        
        analysis = await intel.analyze_instance(
            provider=provider,
            instance_type=instance_type,
            hours_per_month=730
        )
        
        if not analysis.get("success"):
            raise HTTPException(status_code=404, detail=analysis.get("error"))
        
        # Simplified response
        spot_analysis = analysis.get("spot_analysis", {})
        on_demand = analysis.get("on_demand", {})
        
        return {
            "provider": provider,
            "instance_type": instance_type,
            "on_demand_monthly": on_demand.get("monthly", 0),
            "spot_avg_monthly": spot_analysis.get("average", {}).get("monthly", 0),
            "savings_percent": spot_analysis.get("savings", {}).get("percent", 0),
            "savings_monthly": spot_analysis.get("savings", {}).get("monthly_amount", 0),
            "risk_level": spot_analysis.get("risk", {}).get("level", "unknown"),
            "best_region": spot_analysis.get("best_regions", [{}])[0].get("region", "N/A") if spot_analysis.get("best_regions") else "N/A"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Quick check failed: {str(e)}"
        )


@router.get("/history")
async def get_spot_price_history(
    provider: str = Query(..., description="Cloud provider (aws, gcp, azure)"),
    instance_type: str = Query(..., description="Instance type (e.g., m5.xlarge)"),
    region: str = Query(..., description="Region"),
    days: int = Query(7, ge=1, le=90, description="Number of days of history"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get historical spot price data
    
    Returns real historical spot prices collected by the weekly cron job.
    This data is used for:
    - Price trend charts (7d, 30d, 90d)
    - Volatility analysis
    - Interruption frequency calculation
    - Best launch time recommendations
    
    **Data Collection:**
    - Prices are collected weekly via automated cron job
    - Real prices from AWS API, GCP documented rates, Azure Retail API
    - Stored in spot_price_history table
    
    **Note:** Historical data may be limited for new instance types.
    The longer the cron job runs, the more accurate the analysis becomes.
    
    Example:
    `/api/v1/spot-intelligence/history?provider=aws&instance_type=m5.xlarge&region=us-east-1&days=30`
    """
    try:
        from src.models.cloud_provider import SpotPriceHistory
        from sqlalchemy import select
        from datetime import datetime, timedelta
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Query spot_price_history table
        result = await db.execute(
            select(SpotPriceHistory)
            .where(
                SpotPriceHistory.provider == provider,
                SpotPriceHistory.instance_type == instance_type,
                SpotPriceHistory.region == region,
                SpotPriceHistory.timestamp >= start_date
            )
            .order_by(SpotPriceHistory.timestamp.asc())
        )
        
        history = result.scalars().all()
        
        if not history:
            raise HTTPException(
                status_code=404,
                detail=f"No historical spot pricing data for {provider} {instance_type} in {region}. " +
                       "Historical data is collected weekly. Check back after the next collection cycle."
            )
        
        # Format response
        price_points = [
            {
                "timestamp": h.timestamp.isoformat(),
                "spot_price": float(h.spot_price),
                "zone": h.zone,
                "os_type": h.os_type
            }
            for h in history
        ]
        
        # Calculate statistics
        prices = [float(h.spot_price) for h in history]
        avg_price = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)
        
        return {
            "provider": provider,
            "instance_type": instance_type,
            "region": region,
            "days_requested": days,
            "data_points": len(price_points),
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "statistics": {
                "average": round(avg_price, 6),
                "minimum": round(min_price, 6),
                "maximum": round(max_price, 6),
                "volatility": round((max_price - min_price) / avg_price * 100, 2) if avg_price > 0 else 0
            },
            "history": price_points,
            "collection_info": {
                "frequency": "Weekly (every Sunday at midnight UTC)",
                "source": "Real prices from cloud provider APIs",
                "note": "More data will be available over time as the cron job continues to collect prices"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch spot price history: {str(e)}"
        )

