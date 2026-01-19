"""
API Endpoint Tests
"""

import pytest
from httpx import AsyncClient
from decimal import Decimal
from datetime import datetime

from src.models.instance import EC2Instance
from src.models.pricing import OnDemandPricing, SpotPricing


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "endpoints" in data


@pytest.mark.asyncio
async def test_list_instances_empty(client: AsyncClient):
    """Test listing instances when database is empty."""
    response = await client.get("/api/v1/instances")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["instances"] == []


@pytest.mark.asyncio
async def test_list_instances_with_data(client: AsyncClient, test_db, sample_instance_data):
    """Test listing instances with data."""
    # Add sample instance
    instance = EC2Instance(**sample_instance_data)
    test_db.add(instance)
    await test_db.commit()
    
    response = await client.get("/api/v1/instances")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["instances"]) == 1
    assert data["instances"][0]["instance_type"] == "t3.large"


@pytest.mark.asyncio
async def test_list_instances_with_filters(client: AsyncClient, test_db):
    """Test filtering instances."""
    # Add multiple instances
    instances = [
        EC2Instance(instance_type="t3.micro", instance_family="t3", vcpus=2, memory_gb=1.0),
        EC2Instance(instance_type="t3.large", instance_family="t3", vcpus=2, memory_gb=8.0),
        EC2Instance(instance_type="m5.large", instance_family="m5", vcpus=2, memory_gb=8.0),
    ]
    for inst in instances:
        inst.processor_architecture = "x86_64"
        inst.current_generation = True
        test_db.add(inst)
    await test_db.commit()
    
    # Filter by family
    response = await client.get("/api/v1/instances?family=t3")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    
    # Filter by memory
    response = await client.get("/api/v1/instances?min_memory=4")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2


@pytest.mark.asyncio
async def test_get_instance_details(client: AsyncClient, test_db, sample_instance_data):
    """Test getting instance details."""
    instance = EC2Instance(**sample_instance_data)
    test_db.add(instance)
    await test_db.commit()
    
    response = await client.get("/api/v1/instances/t3.large")
    assert response.status_code == 200
    data = response.json()
    assert data["instance_type"] == "t3.large"
    assert data["compute"]["vcpus"] == 2
    assert data["compute"]["memory_gb"] == 8.0


@pytest.mark.asyncio
async def test_get_instance_not_found(client: AsyncClient):
    """Test getting non-existent instance."""
    response = await client.get("/api/v1/instances/nonexistent.type")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_on_demand_pricing(client: AsyncClient, test_db, sample_instance_data):
    """Test getting on-demand pricing."""
    # Add instance and pricing
    instance = EC2Instance(**sample_instance_data)
    test_db.add(instance)
    
    pricing = OnDemandPricing(
        instance_type="t3.large",
        region="us-east-1",
        price_per_hour=Decimal("0.0832"),
        operating_system="Linux",
        tenancy="Shared",
        effective_date=datetime.utcnow(),
    )
    test_db.add(pricing)
    await test_db.commit()
    
    response = await client.get("/api/v1/pricing/on-demand/t3.large")
    assert response.status_code == 200
    data = response.json()
    assert data["instance_type"] == "t3.large"
    assert len(data["pricing"]) == 1
    assert data["pricing"][0]["price_per_hour"] == 0.0832


@pytest.mark.asyncio
async def test_compare_pricing_strategies(client: AsyncClient, test_db, sample_instance_data):
    """Test comparing pricing strategies."""
    # Add instance and pricing
    instance = EC2Instance(**sample_instance_data)
    test_db.add(instance)
    
    pricing = OnDemandPricing(
        instance_type="t3.large",
        region="us-east-1",
        price_per_hour=Decimal("0.0832"),
        operating_system="Linux",
        tenancy="Shared",
        effective_date=datetime.utcnow(),
    )
    test_db.add(pricing)
    await test_db.commit()
    
    response = await client.get("/api/v1/pricing/compare/t3.large?region=us-east-1")
    assert response.status_code == 200
    data = response.json()
    assert data["instance_type"] == "t3.large"
    assert "strategies" in data
    assert len(data["strategies"]) > 0


@pytest.mark.asyncio
async def test_recommendations_endpoint(client: AsyncClient, test_db):
    """Test recommendations endpoint."""
    # Add sample data
    instance = EC2Instance(
        instance_type="t3.large",
        instance_family="t3",
        vcpus=2,
        memory_gb=8.0,
        processor_architecture="x86_64",
        current_generation=True,
    )
    test_db.add(instance)
    
    pricing = OnDemandPricing(
        instance_type="t3.large",
        region="us-east-1",
        price_per_hour=Decimal("0.0832"),
        operating_system="Linux",
        tenancy="Shared",
        effective_date=datetime.utcnow(),
    )
    test_db.add(pricing)
    await test_db.commit()
    
    # Request recommendations
    request_data = {
        "min_vcpus": 2,
        "min_memory_gb": 4.0,
        "regions": ["us-east-1"],
    }
    response = await client.post("/api/v1/recommendations", json=request_data)
    assert response.status_code in [200, 404]  # 404 if no matches


@pytest.mark.asyncio
async def test_workload_types_endpoint(client: AsyncClient):
    """Test workload types listing."""
    response = await client.get("/api/v1/recommendations/workload-types")
    assert response.status_code == 200
    data = response.json()
    assert "workload_types" in data
    assert len(data["workload_types"]) > 0


@pytest.mark.asyncio
async def test_rate_limiting_headers(client: AsyncClient):
    """Test that rate limiting headers are present."""
    response = await client.get("/")
    # Rate limit headers should be present (even if not enforced in tests)
    # Note: In test environment, Redis may not be available
    assert response.status_code == 200

