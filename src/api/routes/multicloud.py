"""
Multi-Cloud API Endpoints
Provides cross-cloud comparison and recommendations.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models.cloud_provider import CloudProvider, CloudInstance, CloudPricing
from src.services.multicloud_recommender import MultiCloudRecommender, MultiCloudRequirements

router = APIRouter(prefix="/multicloud", tags=["Multi-Cloud"])


@router.get("/stats")
async def get_cloud_stats(
    provider: Optional[str] = Query(None, description="Filter by provider (aws, gcp, azure)"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get statistics about available cloud instances and pricing.
    
    Args:
        provider: Optional provider filter (aws, gcp, azure)
        
    Returns:
        Statistics including instance counts, regions, and pricing data
    """
    from sqlalchemy import and_, distinct
    
    # Build base query
    conditions = []
    if provider:
        conditions.append(CloudInstance.provider == provider)
    
    base_where = and_(*conditions) if conditions else True
    
    # Get instance counts by provider
    provider_counts_query = select(
        CloudInstance.provider,
        func.count(CloudInstance.id).label("count")
    ).where(base_where).group_by(CloudInstance.provider)
    
    result = await db.execute(provider_counts_query)
    provider_counts = {row.provider: row.count for row in result.all()}
    
    # Get total instances
    total_query = select(func.count(CloudInstance.id)).where(base_where)
    total_result = await db.execute(total_query)
    total_instances = total_result.scalar() or 0
    
    # Get unique regions count
    regions_query = select(func.count(distinct(CloudPricing.region)))
    if provider:
        regions_query = regions_query.where(CloudPricing.provider == provider)
    regions_result = await db.execute(regions_query)
    regions_count = regions_result.scalar() or 0
    
    # Get pricing records count
    pricing_query = select(func.count(CloudPricing.id))
    if provider:
        pricing_query = pricing_query.where(CloudPricing.provider == provider)
    pricing_result = await db.execute(pricing_query)
    pricing_count = pricing_result.scalar() or 0
    
    return {
        "total_instances": total_instances,
        "by_provider": provider_counts,
        "total_regions": regions_count,
        "total_pricing_records": pricing_count,
        "filter": provider or "all",
    }


class MultiCloudRecommendationRequest(BaseModel):
    """Request model for multi-cloud recommendations."""
    
    min_vcpus: int = Field(..., ge=1, description="Minimum required vCPUs")
    min_memory_gb: float = Field(..., ge=0.5, description="Minimum required memory in GB")
    max_vcpus: Optional[int] = Field(None, description="Maximum vCPUs")
    max_memory_gb: Optional[float] = Field(None, description="Maximum memory in GB")
    
    providers: Optional[List[str]] = Field(
        None,
        description="Cloud providers to include (aws, gcp, azure). Null = all"
    )
    
    aws_regions: Optional[List[str]] = Field(None, description="AWS regions to consider")
    gcp_regions: Optional[List[str]] = Field(None, description="GCP regions to consider")
    azure_regions: Optional[List[str]] = Field(None, description="Azure regions to consider")
    
    workload_type: str = Field("steady", description="Workload type: steady, variable, burst, batch")
    spot_eligible: bool = Field(False, description="Consider spot/preemptible instances")
    hours_per_month: int = Field(730, ge=1, le=744, description="Expected monthly usage hours")
    
    max_hourly_cost: Optional[float] = Field(None, description="Maximum hourly cost")
    max_monthly_budget: Optional[float] = Field(None, description="Maximum monthly budget")
    
    requires_gpu: bool = Field(False, description="Requires GPU")
    gpu_type: Optional[str] = Field(None, description="Preferred GPU type")
    exclude_burstable: bool = Field(False, description="Exclude burstable instances")
    
    class Config:
        json_schema_extra = {
            "example": {
                "min_vcpus": 4,
                "min_memory_gb": 16,
                "providers": ["aws", "gcp", "azure"],
                "workload_type": "steady",
                "spot_eligible": True,
                "hours_per_month": 730,
                "max_monthly_budget": 200
            }
        }


@router.post("/recommendations")
async def get_multicloud_recommendations(
    request: MultiCloudRecommendationRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get cost-optimized recommendations across AWS, GCP, and Azure.
    
    Compares equivalent instances across all major cloud providers
    and returns the most cost-effective options.
    
    Returns:
        Multi-cloud recommendations with cross-cloud comparison
    """
    requirements = MultiCloudRequirements(
        min_vcpus=request.min_vcpus,
        min_memory_gb=request.min_memory_gb,
        max_vcpus=request.max_vcpus,
        max_memory_gb=request.max_memory_gb,
        providers=request.providers,
        aws_regions=request.aws_regions,
        gcp_regions=request.gcp_regions,
        azure_regions=request.azure_regions,
        workload_type=request.workload_type,
        spot_eligible=request.spot_eligible,
        hours_per_month=request.hours_per_month,
        max_hourly_cost=request.max_hourly_cost,
        max_monthly_budget=request.max_monthly_budget,
        requires_gpu=request.requires_gpu,
        gpu_type=request.gpu_type,
        exclude_burstable=request.exclude_burstable,
    )
    
    recommender = MultiCloudRecommender(db)
    recommendations = await recommender.generate_recommendations(requirements)
    
    if "error" in recommendations:
        raise HTTPException(status_code=404, detail=recommendations["error"])
    
    return recommendations


@router.get("/instances")
async def list_multicloud_instances(
    provider: Optional[str] = Query(None, description="Filter by provider (aws, gcp, azure)"),
    min_vcpus: Optional[int] = Query(None, description="Minimum vCPUs"),
    max_vcpus: Optional[int] = Query(None, description="Maximum vCPUs"),
    min_memory: Optional[float] = Query(None, description="Minimum memory GB"),
    max_memory: Optional[float] = Query(None, description="Maximum memory GB"),
    category: Optional[str] = Query(None, description="Instance category"),
    has_gpu: Optional[bool] = Query(None, description="Filter for GPU instances"),
    limit: int = Query(50, le=10000, description="Maximum results"),
    offset: int = Query(0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    List instances across all cloud providers.
    
    Returns paginated list of instances from AWS, GCP, and Azure.
    
    Optimized with:
    - Single JOIN query instead of N+1 queries
    - Database indexes on frequently queried columns
    """
    # Build query with LEFT JOIN to get pricing in one query
    from sqlalchemy.orm import aliased
    
    # Subquery to get the cheapest on-demand pricing per instance
    pricing_subquery = (
        select(
            CloudPricing.provider,
            CloudPricing.instance_type,
            func.min(CloudPricing.hourly_price).label('min_price')
        )
        .where(CloudPricing.pricing_type == "on_demand")
        .group_by(CloudPricing.provider, CloudPricing.instance_type)
        .subquery()
    )
    
    # Main query with JOIN
    query = select(
        CloudInstance,
        pricing_subquery.c.min_price.label('hourly_price')
    ).outerjoin(
        pricing_subquery,
        and_(
            CloudInstance.provider == pricing_subquery.c.provider,
            CloudInstance.instance_type == pricing_subquery.c.instance_type
        )
    )
    
    conditions = []
    
    if provider:
        conditions.append(CloudInstance.provider == provider)
    if min_vcpus:
        conditions.append(CloudInstance.vcpus >= min_vcpus)
    if max_vcpus:
        conditions.append(CloudInstance.vcpus <= max_vcpus)
    if min_memory:
        conditions.append(CloudInstance.memory_gb >= min_memory)
    if max_memory:
        conditions.append(CloudInstance.memory_gb <= max_memory)
    if category:
        conditions.append(CloudInstance.category == category)
    if has_gpu is not None:
        if has_gpu:
            conditions.append(CloudInstance.gpu_count > 0)
        else:
            conditions.append(
                (CloudInstance.gpu_count == None) | (CloudInstance.gpu_count == 0)
            )
    
    if conditions:
        query = query.where(*conditions)
    
    # Get total count (before pagination)
    count_query = select(func.count()).select_from(
        select(CloudInstance).where(*conditions).subquery()
    ) if conditions else select(func.count()).select_from(CloudInstance)
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination and ordering
    query = query.order_by(CloudInstance.provider, CloudInstance.vcpus, CloudInstance.memory_gb)
    query = query.offset(offset).limit(limit)
    
    # Execute query once
    result = await db.execute(query)
    rows = result.all()
    
    # Format response
    instance_data = []
    for instance, hourly_price in rows:
        instance_dict = instance.to_dict()
        instance_dict["hourly_price"] = float(hourly_price) if hourly_price else 0.0
        instance_data.append(instance_dict)
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "instances": instance_data,
    }


@router.get("/instances/{provider}/{instance_type}")
async def get_instance_details(
    provider: str,
    instance_type: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get detailed information about a specific instance type.
    
    Args:
        provider: Cloud provider (aws, gcp, azure)
        instance_type: Instance type identifier
        
    Returns:
        Instance details with pricing across regions
    """
    # Get instance
    instance_query = select(CloudInstance).where(
        CloudInstance.provider == provider,
        CloudInstance.instance_type == instance_type,
    )
    result = await db.execute(instance_query)
    instance = result.scalar_one_or_none()
    
    if not instance:
        raise HTTPException(
            status_code=404,
            detail=f"Instance {instance_type} not found for provider {provider}"
        )
    
    # Get pricing
    pricing_query = select(CloudPricing).where(
        CloudPricing.provider == provider,
        CloudPricing.instance_type == instance_type,
    ).order_by(CloudPricing.region, CloudPricing.pricing_type)
    
    pricing_result = await db.execute(pricing_query)
    pricing = pricing_result.scalars().all()
    
    # Group pricing by region
    pricing_by_region = {}
    for p in pricing:
        if p.region not in pricing_by_region:
            pricing_by_region[p.region] = {}
        pricing_by_region[p.region][p.pricing_type] = {
            "hourly": float(p.hourly_price),
            "monthly": float(p.monthly_price) if p.monthly_price else None,
        }
    
    return {
        "provider": provider,
        "instance": instance.to_dict(),
        "pricing_by_region": pricing_by_region,
    }


@router.get("/compare/{instance_type}")
async def find_equivalent_instances(
    instance_type: str,
    provider: str = Query(..., description="Source provider (aws, gcp, azure)"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Find equivalent instances across cloud providers.
    
    Given an instance type from one provider, finds similar instances
    in other cloud providers based on specs.
    
    Args:
        instance_type: Source instance type
        provider: Source cloud provider
        
    Returns:
        Equivalent instances in other providers
    """
    recommender = MultiCloudRecommender(db)
    equivalents = await recommender.find_equivalent_instances(instance_type, provider)
    
    if "error" in equivalents:
        raise HTTPException(status_code=404, detail=equivalents["error"])
    
    return equivalents


@router.get("/pricing/compare")
async def compare_pricing_across_clouds(
    vcpus: int = Query(..., ge=1, description="Required vCPUs"),
    memory_gb: float = Query(..., ge=0.5, description="Required memory in GB"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Compare pricing across clouds for similar instance specs.
    
    Finds the cheapest options in each cloud for given specs.
    
    Args:
        vcpus: Required vCPUs
        memory_gb: Required memory in GB
        
    Returns:
        Pricing comparison across AWS, GCP, and Azure
    """
    comparison = {}
    
    for provider in ["aws", "gcp", "azure"]:
        # Find matching instances
        instance_query = select(CloudInstance).where(
            CloudInstance.provider == provider,
            CloudInstance.vcpus >= vcpus,
            CloudInstance.vcpus <= vcpus * 1.5,
            CloudInstance.memory_gb >= memory_gb,
            CloudInstance.memory_gb <= memory_gb * 1.5,
        )
        result = await db.execute(instance_query)
        instances = result.scalars().all()
        
        if not instances:
            comparison[provider] = {"available": False}
            continue
        
        instance_types = [i.instance_type for i in instances]
        
        # Get on-demand pricing
        pricing_query = select(CloudPricing).where(
            CloudPricing.provider == provider,
            CloudPricing.instance_type.in_(instance_types),
            CloudPricing.pricing_type == "on_demand",
        ).order_by(CloudPricing.hourly_price).limit(1)
        
        pricing_result = await db.execute(pricing_query)
        cheapest = pricing_result.scalar_one_or_none()
        
        if cheapest:
            instance = next(i for i in instances if i.instance_type == cheapest.instance_type)
            comparison[provider] = {
                "available": True,
                "cheapest_instance": cheapest.instance_type,
                "specs": {
                    "vcpus": instance.vcpus,
                    "memory_gb": instance.memory_gb,
                },
                "region": cheapest.region,
                "hourly_price": float(cheapest.hourly_price),
                "monthly_price": float(cheapest.hourly_price * 730),
            }
        else:
            comparison[provider] = {"available": False}
    
    # Find overall cheapest
    available = {k: v for k, v in comparison.items() if v.get("available")}
    if available:
        cheapest = min(available.keys(), key=lambda k: available[k]["hourly_price"])
        comparison["cheapest_overall"] = {
            "provider": cheapest,
            "instance": available[cheapest]["cheapest_instance"],
            "monthly_cost": available[cheapest]["monthly_price"],
        }
    
    return {
        "requirements": {
            "vcpus": vcpus,
            "memory_gb": memory_gb,
        },
        "comparison": comparison,
    }


@router.get("/providers")
async def list_providers() -> dict:
    """
    List supported cloud providers with details.
    
    Returns:
        Information about supported cloud providers
    """
    return {
        "providers": [
            {
                "id": "aws",
                "name": "Amazon Web Services",
                "instance_prefix": "EC2",
                "spot_name": "Spot Instances",
                "reserved_name": "Reserved Instances",
                "regions_count": 17,
            },
            {
                "id": "gcp",
                "name": "Google Cloud Platform",
                "instance_prefix": "Compute Engine",
                "spot_name": "Preemptible/Spot VMs",
                "reserved_name": "Committed Use Discounts",
                "regions_count": 28,
            },
            {
                "id": "azure",
                "name": "Microsoft Azure",
                "instance_prefix": "Virtual Machines",
                "spot_name": "Spot VMs",
                "reserved_name": "Reserved VM Instances",
                "regions_count": 34,
            },
        ]
    }


@router.get("/categories")
async def list_instance_categories(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    List instance categories across all providers.
    
    Returns:
        Categories with instance counts per provider
    """
    query = select(
        CloudInstance.provider,
        CloudInstance.category,
        func.count(CloudInstance.id).label("count"),
    ).group_by(
        CloudInstance.provider,
        CloudInstance.category,
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    categories = {}
    for row in rows:
        if row.category not in categories:
            categories[row.category] = {"aws": 0, "gcp": 0, "azure": 0}
        categories[row.category][row.provider] = row.count
    
    return {
        "categories": [
            {
                "name": cat,
                "counts": counts,
                "total": sum(counts.values()),
            }
            for cat, counts in categories.items()
        ]
    }

