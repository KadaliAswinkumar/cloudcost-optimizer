"""
Pytest configuration and fixtures.
"""

from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.api.main import app
from src.core.database import Base, get_db

# Register all ORM models with Base.metadata before create_all
import src.models  # noqa: F401, E402

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """In-memory SQLite for API tests."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """HTTP client against the ASGI app with DB override."""

    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def sample_instance_data() -> dict:
    """Sample EC2 instance row."""
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
    """Sample on-demand pricing row."""
    return {
        "instance_type": "t3.large",
        "region": "us-east-1",
        "price_per_hour": "0.0832",
        "operating_system": "Linux",
        "tenancy": "Shared",
    }
