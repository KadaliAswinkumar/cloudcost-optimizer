"""
EC2 Instance Endpoints
Provides access to EC2 instance specifications and metadata.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.cache import cache_service, CacheKeys
from src.models.instance import EC2Instance

router = APIRouter(prefix="/instances", tags=["Instances"])


@router.get("", response_model=None)
async def list_instances(
    family: Optional[str] = Query(None, description="Filter by instance family (e.g., t3, m5)"),
    min_vcpus: Optional[int] = Query(None, description="Minimum vCPUs"),
    max_vcpus: Optional[int] = Query(None, description="Maximum vCPUs"),
    min_memory: Optional[float] = Query(None, description="Minimum memory in GB"),
    max_memory: Optional[float] = Query(None, description="Maximum memory in GB"),
    architecture: Optional[str] = Query("x86_64", description="Processor architecture"),
    current_gen: Optional[bool] = Query(True, description="Current generation only"),
    has_gpu: Optional[bool] = Query(None, description="Filter for GPU instances"),
    limit: int = Query(50, le=200, description="Maximum results"),
    offset: int = Query(0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    List EC2 instance types with filtering.
    
    Returns paginated list of instances matching the specified criteria.
    """
    # Build query
    query = select(EC2Instance)
    conditions = []
    
    if family:
        conditions.append(EC2Instance.instance_family == family)
    if min_vcpus:
        conditions.append(EC2Instance.vcpus >= min_vcpus)
    if max_vcpus:
        conditions.append(EC2Instance.vcpus <= max_vcpus)
    if min_memory:
        conditions.append(EC2Instance.memory_gb >= min_memory)
    if max_memory:
        conditions.append(EC2Instance.memory_gb <= max_memory)
    if architecture:
        conditions.append(EC2Instance.processor_architecture == architecture)
    if current_gen is not None:
        conditions.append(EC2Instance.current_generation == current_gen)
    if has_gpu is not None:
        if has_gpu:
            conditions.append(EC2Instance.gpu_count > 0)
        else:
            conditions.append(
                (EC2Instance.gpu_count == None) | (EC2Instance.gpu_count == 0)
            )
    
    if conditions:
        query = query.where(*conditions)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    query = query.order_by(EC2Instance.vcpus, EC2Instance.memory_gb)
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    instances = result.scalars().all()
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "instances": [i.to_dict() for i in instances],
    }


@router.get("/families")
async def list_instance_families(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    List all available instance families with counts.
    
    Returns grouped instance family information.
    """
    query = select(
        EC2Instance.instance_family,
        func.count(EC2Instance.id).label("count"),
        func.min(EC2Instance.vcpus).label("min_vcpus"),
        func.max(EC2Instance.vcpus).label("max_vcpus"),
        func.min(EC2Instance.memory_gb).label("min_memory"),
        func.max(EC2Instance.memory_gb).label("max_memory"),
    ).group_by(EC2Instance.instance_family).order_by(EC2Instance.instance_family)
    
    result = await db.execute(query)
    families = result.all()
    
    # Categorize families
    categories = {
        "general": ["t", "m", "mac"],
        "compute": ["c"],
        "memory": ["r", "x", "z"],
        "storage": ["d", "h", "i"],
        "accelerated": ["p", "g", "inf", "trn", "dl"],
        "hpc": ["hpc"],
    }
    
    family_list = []
    for row in families:
        category = "other"
        for cat, prefixes in categories.items():
            if any(row.instance_family.startswith(p) for p in prefixes):
                category = cat
                break
        
        family_list.append({
            "family": row.instance_family,
            "category": category,
            "instance_count": row.count,
            "vcpu_range": [row.min_vcpus, row.max_vcpus],
            "memory_range_gb": [row.min_memory, row.max_memory],
        })
    
    return {
        "total_families": len(family_list),
        "families": family_list,
    }


@router.get("/{instance_type}")
async def get_instance_details(
    instance_type: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get detailed specifications for a specific instance type.
    
    Args:
        instance_type: EC2 instance type (e.g., t3.large)
        
    Returns:
        Detailed instance specifications
    """
    query = select(EC2Instance).where(EC2Instance.instance_type == instance_type)
    result = await db.execute(query)
    instance = result.scalar_one_or_none()
    
    if not instance:
        raise HTTPException(status_code=404, detail=f"Instance type '{instance_type}' not found")
    
    return {
        "instance_type": instance.instance_type,
        "instance_family": instance.instance_family,
        "generation": instance.generation,
        "compute": {
            "vcpus": instance.vcpus,
            "memory_gb": instance.memory_gb,
            "memory_per_vcpu": instance.memory_per_vcpu,
        },
        "processor": {
            "architecture": instance.processor_architecture,
            "physical_processor": instance.physical_processor,
            "clock_speed_ghz": instance.clock_speed_ghz,
        },
        "storage": {
            "type": instance.storage_type,
            "instance_storage_gb": instance.instance_storage_gb,
            "ebs_bandwidth_mbps": instance.ebs_bandwidth_mbps,
        },
        "network": {
            "performance": instance.network_performance,
        },
        "gpu": {
            "count": instance.gpu_count,
            "memory_gb": instance.gpu_memory_gb,
            "manufacturer": instance.gpu_manufacturer,
            "name": instance.gpu_name,
        } if instance.gpu_count else None,
        "features": {
            "current_generation": instance.current_generation,
            "bare_metal": instance.bare_metal,
            "hypervisor": instance.hypervisor,
        },
    }


@router.get("/{instance_type}/compare")
async def compare_instances(
    instance_type: str,
    compare_with: List[str] = Query(..., description="Instance types to compare"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Compare multiple instance types side by side.
    
    Args:
        instance_type: Base instance type
        compare_with: List of instance types to compare
        
    Returns:
        Comparison matrix
    """
    all_types = [instance_type] + compare_with
    
    query = select(EC2Instance).where(EC2Instance.instance_type.in_(all_types))
    result = await db.execute(query)
    instances = {i.instance_type: i for i in result.scalars().all()}
    
    # Check for missing instances
    missing = [t for t in all_types if t not in instances]
    if missing:
        raise HTTPException(
            status_code=404,
            detail=f"Instance types not found: {', '.join(missing)}"
        )
    
    comparison = []
    for t in all_types:
        i = instances[t]
        comparison.append({
            "instance_type": i.instance_type,
            "vcpus": i.vcpus,
            "memory_gb": i.memory_gb,
            "memory_per_vcpu": round(i.memory_per_vcpu, 2),
            "storage_type": i.storage_type,
            "network_performance": i.network_performance,
            "current_generation": i.current_generation,
        })
    
    return {
        "comparison": comparison,
        "summary": {
            "vcpu_range": [min(c["vcpus"] for c in comparison), max(c["vcpus"] for c in comparison)],
            "memory_range": [min(c["memory_gb"] for c in comparison), max(c["memory_gb"] for c in comparison)],
        }
    }

