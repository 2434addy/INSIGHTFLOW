"""
Shared test fixtures for the InsightFlow backend test suite.

Provides:
- Async test client (httpx)
- In-memory test database
- Authenticated user fixtures
- Organization fixtures
"""

import asyncio
from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.database import get_db
from app.core.security import create_access_token, hash_password
from app.main import create_app
from app.models.base import Base
from app.models.user import User
from app.models.organization import Membership, Organization

# Use SQLite for fast in-memory tests
# For integration tests that need PostgreSQL features, use a test PostgreSQL instance
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session_factory = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create tables before each test, drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def get_test_db() -> AsyncGenerator[AsyncSession, None]:
    """Override database dependency for tests."""
    async with test_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Direct database session for test setup."""
    async with test_session_factory() as session:
        yield session
        await session.commit()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP test client with database override."""
    app = create_app()
    app.dependency_overrides[get_db] = get_test_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user in the database."""
    user = User(
        id=uuid4(),
        email="testuser@agency.com",
        password_hash=hash_password("SecureP@ssw0rd123"),
        full_name="Test User",
        auth_provider="email",
        email_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def test_organization(db_session: AsyncSession, test_user: User) -> Organization:
    """Create a test organization owned by test_user."""
    organization = Organization(
        id=uuid4(),
        name="Test Agency",
        slug="test-agency",
        owner_id=test_user.id,
        plan="starter",
    )
    db_session.add(organization)
    await db_session.commit()

    membership = Membership(
        id=uuid4(),
        user_id=test_user.id,
        organization_id=organization.id,
        role="owner",
    )
    db_session.add(membership)
    await db_session.commit()

    return organization


@pytest_asyncio.fixture
async def auth_headers(test_user: User, test_organization: Organization) -> dict[str, str]:
    """Authorization headers with a valid access token."""
    token = create_access_token(
        user_id=test_user.id,
        organization_id=test_organization.id,
    )
    return {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(test_organization.id),
    }


@pytest_asyncio.fixture
async def other_user(db_session: AsyncSession) -> User:
    """Create a second user for tenant isolation tests."""
    user = User(
        id=uuid4(),
        email="otheruser@different-agency.com",
        password_hash=hash_password("OtherP@ssw0rd456"),
        full_name="Other User",
        auth_provider="email",
        email_verified=True,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def other_organization(db_session: AsyncSession, other_user: User) -> Organization:
    """Create an organization for the other user (tenant isolation testing)."""
    organization = Organization(
        id=uuid4(),
        name="Other Agency",
        slug="other-agency",
        owner_id=other_user.id,
        plan="starter",
    )
    db_session.add(organization)
    await db_session.flush()

    membership = Membership(
        id=uuid4(),
        user_id=other_user.id,
        organization_id=organization.id,
        role="owner",
    )
    db_session.add(membership)
    await db_session.flush()

    return organization
