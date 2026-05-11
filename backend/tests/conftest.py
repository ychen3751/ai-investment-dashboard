"""Shared fixtures for backend tests.

Session-scoped tables for loop safety.  Each test request gets a fresh
per-request database session via dependency override.
"""
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.base import Base
from app.db.session import engine, get_db
from app.main import app
# Import all models so Base.metadata is fully populated for create_all/drop_all
from app.models import *  # noqa: F403, F401
from app.core.security import create_access_token

TestSessionFactory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session")
async def setup_db():
    """Drop and recreate all tables for a clean test session."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    return True


@pytest_asyncio.fixture
async def client(setup_db):
    """Test client — each request gets a fresh DB session."""
    async def _get_test_db() -> AsyncGenerator[AsyncSession, None]:
        async with TestSessionFactory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_db] = _get_test_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict:
    """Register a unique user and return Bearer auth headers."""
    uid = str(uuid.uuid4())[:8]
    res = await client.post(
        "/api/auth/register",
        json={"email": f"test_{uid}@example.com", "username": f"user_{uid}", "password": "testpass123"},
    )
    data = res.json()
    token = data.get("access_token") or create_access_token({"sub": str(uuid.uuid4())})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def test_token() -> str:
    """Generate a JWT without hitting the DB (for unit tests)."""
    return create_access_token({"sub": str(uuid.uuid4())})
