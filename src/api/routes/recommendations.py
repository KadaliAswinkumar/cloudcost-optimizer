"""
Recommendation Endpoints
Provides intelligent instance recommendations based on workload requirements.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models.recommendation import WorkloadType, InterruptionTolerance
from src.services.recommendation_engine import RecommendationEngine, WorkloadRequirements

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


class RecommendationRequest(BaseModel):
    """Request model for instance recommendations."""
    
    min_vcpus: int = Field(..., ge=1, description="Minimum required vCPUs")
    min_memory_gb: float = Field(..., ge=0.5, description="Minimum required memory in GB")
    max_vcpus: Optional[int] = Field(None, description="Maximum vCPUs (for right-sizing)")
    max_memory_gb: Optional[float] = Field(None, description="Maximum memory in GB")
    
    workload_type: WorkloadType = Field(
        WorkloadType.STEADY,
        description="Type of workload pattern"
    )
    interruption_tolerance: InterruptionTolerance = Field(
        InterruptionTolerance.NONE,
        description="Tolerance for Spot interruptions"
    )
    
    hours_per_month: int = Field(730, ge=1, le=744, description="Expected monthly usage hours")
    regions: Optional[List[str]] = Field(None, description="Preferred AWS regions")
    
    max_hourly_cost: Optional[float] = Field(None, description="Maximum hourly cost constraint")
    max_monthly_budget: Optional[float] = Field(None, description="Maximum monthly budget")
    
    requires_gpu: bool = Field(False, description="Requires GPU instances")
    architecture: str = Field("x86_64", description="Processor architecture (x86_64 or arm64)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "min_vcpus": 4,
                "min_memory_gb": 8,
                "workload_type": "steady",
                "interruption_tolerance": "low",
                "hours_per_month": 730,
                "regions": ["us-east-1", "us-west-2"],
                "max_monthly_budget": 200,
            }
        }


class QuickRecommendationRequest(BaseModel):
    """Simplified request for quick recommendations."""
    
    vcpus: int = Field(..., ge=1, description="Required vCPUs")
    memory_gb: float = Field(..., ge=0.5, description="Required memory in GB")
    region: str = Field("us-east-1", description="Target region")
    
    class Config:
        json_schema_extra = {
            "example": {
                "vcpus": 2,
                "memory_gb": 4,
                "region": "us-east-1",
            }
        }


@router.post("")
async def get_recommendations(
    request: RecommendationRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get instance recommendations based on workload requirements.
    
    Analyzes your requirements and returns ranked recommendations
    across different pricing strategies (On-Demand, Reserved, Spot).
    
    Args:
        request: Workload requirements
        
    Returns:
        Ranked list of instance recommendations
    """
    # Convert to internal format
    requirements = WorkloadRequirements(
        min_vcpus=request.min_vcpus,
        min_memory_gb=request.min_memory_gb,
        max_vcpus=request.max_vcpus,
        max_memory_gb=request.max_memory_gb,
        workload_type=request.workload_type,
        interruption_tolerance=request.interruption_tolerance,
        hours_per_month=request.hours_per_month,
        regions=request.regions,
        max_hourly_cost=request.max_hourly_cost,
        max_monthly_budget=request.max_monthly_budget,
        requires_gpu=request.requires_gpu,
        architecture=request.architecture,
    )
    
    engine = RecommendationEngine(db)
    recommendations = await engine.generate_recommendations(requirements)
    
    if not recommendations:
        raise HTTPException(
            status_code=404,
            detail="No instances found matching your requirements. Try relaxing constraints."
        )
    
    # Calculate summary statistics
    costs = [r["pricing"]["monthly_cost"] for r in recommendations]
    savings = [r["savings"]["percentage"] for r in recommendations]
    
    return {
        "request_summary": {
            "min_vcpus": request.min_vcpus,
            "min_memory_gb": request.min_memory_gb,
            "workload_type": request.workload_type.value,
            "interruption_tolerance": request.interruption_tolerance.value,
            "hours_per_month": request.hours_per_month,
            "regions": request.regions,
        },
        "summary": {
            "total_recommendations": len(recommendations),
            "cost_range": {
                "min": min(costs),
                "max": max(costs),
            },
            "max_savings_percentage": max(savings),
            "best_value": recommendations[0]["instance_type"] if recommendations else None,
        },
        "recommendations": recommendations,
    }


@router.post("/quick")
async def get_quick_recommendation(
    request: QuickRecommendationRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get a quick single recommendation for simple requirements.
    
    Use this for a fast answer when you just need basic specs.
    
    Args:
        request: Basic requirements (vCPUs, memory, region)
        
    Returns:
        Single best recommendation
    """
    engine = RecommendationEngine(db)
    recommendation = await engine.get_quick_recommendation(
        vcpus=request.vcpus,
        memory_gb=request.memory_gb,
        region=request.region,
    )
    
    if "error" in recommendation:
        raise HTTPException(
            status_code=404,
            detail=recommendation["error"]
        )
    
    return {
        "request": {
            "vcpus": request.vcpus,
            "memory_gb": request.memory_gb,
            "region": request.region,
        },
        "recommendation": recommendation,
    }


@router.get("/workload-types")
async def list_workload_types() -> dict:
    """
    List available workload types with descriptions.
    
    Returns:
        Workload type options
    """
    return {
        "workload_types": [
            {
                "value": WorkloadType.STEADY.value,
                "name": "Steady",
                "description": "Consistent load 24/7. Best for production workloads.",
                "recommended_strategy": "Reserved Instances",
            },
            {
                "value": WorkloadType.VARIABLE.value,
                "name": "Variable",
                "description": "Load varies throughout the day/week.",
                "recommended_strategy": "Mix of Reserved and On-Demand",
            },
            {
                "value": WorkloadType.BURST.value,
                "name": "Burst",
                "description": "Occasional high demand spikes.",
                "recommended_strategy": "On-Demand or Spot",
            },
            {
                "value": WorkloadType.BATCH.value,
                "name": "Batch",
                "description": "Batch processing jobs that can be interrupted.",
                "recommended_strategy": "Spot Instances",
            },
            {
                "value": WorkloadType.DEV_TEST.value,
                "name": "Dev/Test",
                "description": "Development and testing environments.",
                "recommended_strategy": "Spot or On-Demand",
            },
        ]
    }


@router.get("/interruption-tolerance")
async def list_interruption_tolerances() -> dict:
    """
    List interruption tolerance levels for Spot instances.
    
    Returns:
        Tolerance level options
    """
    return {
        "tolerance_levels": [
            {
                "value": InterruptionTolerance.NONE.value,
                "name": "None",
                "description": "Cannot tolerate any interruptions. Spot not recommended.",
                "spot_eligible": False,
            },
            {
                "value": InterruptionTolerance.LOW.value,
                "name": "Low",
                "description": "Can handle rare interruptions with checkpointing.",
                "spot_eligible": True,
            },
            {
                "value": InterruptionTolerance.MEDIUM.value,
                "name": "Medium",
                "description": "Can handle occasional interruptions. Jobs can restart.",
                "spot_eligible": True,
            },
            {
                "value": InterruptionTolerance.HIGH.value,
                "name": "High",
                "description": "Fully tolerant of interruptions. Stateless workloads.",
                "spot_eligible": True,
            },
        ]
    }


@router.get("/right-size/{instance_type}")
async def get_right_size_recommendations(
    instance_type: str,
    region: str = Query("us-east-1", description="Target region"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get right-sizing recommendations for an existing instance.
    
    Analyzes if you could use a smaller/different instance type.
    
    Args:
        instance_type: Current instance type
        region: Target region
        
    Returns:
        Right-sizing recommendations
    """
    from src.models.instance import EC2Instance
    from src.models.pricing import OnDemandPricing
    from sqlalchemy import select
    
    # Get current instance specs
    instance_query = select(EC2Instance).where(
        EC2Instance.instance_type == instance_type
    )
    result = await db.execute(instance_query)
    current_instance = result.scalar_one_or_none()
    
    if not current_instance:
        raise HTTPException(
            status_code=404,
            detail=f"Instance type '{instance_type}' not found"
        )
    
    # Get current pricing
    price_query = select(OnDemandPricing).where(
        OnDemandPricing.instance_type == instance_type,
        OnDemandPricing.region == region,
    )
    price_result = await db.execute(price_query)
    current_price = price_result.scalar_one_or_none()
    
    # Find alternatives
    engine = RecommendationEngine(db)
    requirements = WorkloadRequirements(
        min_vcpus=max(1, current_instance.vcpus // 2),  # Allow 50% smaller
        min_memory_gb=max(1, current_instance.memory_gb / 2),
        max_vcpus=current_instance.vcpus * 2,  # Allow 2x larger
        max_memory_gb=current_instance.memory_gb * 2,
        regions=[region],
    )
    
    alternatives = await engine.generate_recommendations(requirements)
    
    # Categorize alternatives
    smaller = []
    similar = []
    larger = []
    
    for alt in alternatives:
        if alt["instance_type"] == instance_type:
            continue
            
        if alt["specs"]["vcpus"] < current_instance.vcpus:
            smaller.append(alt)
        elif alt["specs"]["vcpus"] > current_instance.vcpus:
            larger.append(alt)
        else:
            similar.append(alt)
    
    return {
        "current_instance": {
            "type": instance_type,
            "vcpus": current_instance.vcpus,
            "memory_gb": current_instance.memory_gb,
            "hourly_cost": float(current_price.price_per_hour) if current_price else None,
            "monthly_cost": float(current_price.price_per_hour * 730) if current_price else None,
        },
        "recommendations": {
            "downsize_options": smaller[:3],
            "similar_options": similar[:3],
            "upgrade_options": larger[:3],
        },
        "potential_savings": {
            "if_downsize": smaller[0]["savings"]["amount_monthly"] if smaller else 0,
            "best_alternative": smaller[0]["instance_type"] if smaller else None,
        },
    }

