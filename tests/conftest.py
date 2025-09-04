import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
"""
Test database URL for pytest runs. Uses SQLite in-memory for isolation.
"""

engine_test = create_async_engine(
    TEST_DATABASE_URL,
    future=True,
    echo=False
)
"""
Async engine for test database.
"""

AsyncSessionLocal = sessionmaker(
    engine_test,
    expire_on_commit=False,
    class_=AsyncSession
)
"""
Session factory for async SQLAlchemy sessions in tests.
"""


@pytest_asyncio.fixture(scope="session", autouse=True)
async def init_db():
    """
    Create all tables before tests and drop them after the session.
    Ensures a clean database state for each test run.
    """
    async with engine_test.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session():
    """
    Provide a new async database session for each test.
    Yields:
        AsyncSession: SQLAlchemy async session for DB operations.
    """
    async with AsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    """
    Provide an HTTPX AsyncClient for API testing with DB dependency override.
    Yields:
        AsyncClient: HTTPX client with overridden DB dependency.
    """
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test"
    ) as async_client:
        yield async_client

    app.dependency_overrides.clear()
