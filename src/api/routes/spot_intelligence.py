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

router = APIRouter(tags=["Spot Intelligence™"])


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
