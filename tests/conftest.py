"""
Pytest Configuration and Fixtures
"""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.api.main import app
from src.core.database import Base, get_db


# Test database URL (use SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database override."""
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_instance_data() -> dict:
    """Sample EC2 instance data."""
    return {
        "instance_type": "t3.large",
        "instance_family": "t3",
        "generation": "3",
        "vcpus": 2,
        "memory_gb": 8.0,
        "processor_architecture": "x86_64",
        "storage_type": "EBS-Only",
        "network_performance": "Up to 5 Gigabit",
        "current_generation": True,
    }


@pytest.fixture
def sample_pricing_data() -> dict:
    """Sample pricing data."""
    return {
        "instance_type": "t3.large",
        "region": "us-east-1",
        "price_per_hour": "0.0832",
        "operating_system": "Linux",
        "tenancy": "Shared",
    }

