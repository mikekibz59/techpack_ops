import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from database import Base, get_async_session
from main import app
from models.user import User

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
TEST_USER_EMAIL = "test_user@example.com"
TEST_ADMIN_EMAIL = "test_admin@example.com"
TEST_PASSWORD = "testpassword"
TEST_ADMIN_ROLE = "admin"
TEST_USER_ROLE = "user"

# test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=NullPool,
)

test_async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh database for each test.
    Tables are created before the test and dropped after.
    """

    async with test_engine.connect() as conn:
        async with conn.begin():
            await conn.run_sync(Base.metadata.create_all)

        async_session = async_sessionmaker(
            bind=conn,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with async_session() as session:
            yield session

        async with conn.begin():
            await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with the test database session

    Args:
        db_session (AsyncSession): _description_

    Returns:
        AsyncGenerator[AsyncClient, None]: _description_
    """

    async def override_get_async_session():
        yield db_session

    app.dependency_overrides[get_async_session] = override_get_async_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user in the database

    Args:
        db_session (AsyncSession): as the name suggests.
    """
    from auth import UserManager, get_user_db
    from fastapi_users.password import PasswordHelper

    password_helper = PasswordHelper()
    user = User(
        email=TEST_USER_EMAIL,
        hashed_password=password_helper.hash(TEST_PASSWORD),
        role=TEST_USER_ROLE,
        is_active=True,
        is_superuser=False,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_admin(db_session: AsyncSession) -> User:
    """Create admin user in db

    Args:
        db_session (AsyncSession): as the name suggests
    """
    from auth import UserManager, get_user_db
    from fastapi_users.password import PasswordHelper

    admin = User(
        email=TEST_ADMIN_EMAIL,
        role=TEST_ADMIN_ROLE,
        is_active=True,
        is_superuser=True,
        is_verified=True,
        hashed_password=PasswordHelper().hash(TEST_PASSWORD),
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest.fixture
async def authenticated_client(client: AsyncClient, test_user: User) -> AsyncClient:
    """Create a client with an authenticated regular user

    Args:
        client (AsyncClient): client connecting to the server
        test_user (User): user to be authenticated

    Returns:
        AsyncClient: client with authenticated user
    """

    response = await client.post(
        "/auth/jwt/login",
        data={
            "username": test_user.email,
            "password": TEST_PASSWORD,
        },
    )
    
    token = response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest.fixture
async def admin_client(client: AsyncClient, test_admin: User) -> AsyncClient:
    """Create client iwth authenticated admin user

    Args:
        client (AsyncClient): client connecting to server
        test_admin (User): admin user to be authenticated.

    Returns:
        AsyncClient: client with authenticated admin user
    """
    response = await client.post(
        "auth/jwt/login",
        data={
            "username": test_admin.email,
            "passoword": TEST_PASSWORD,
        },
    )

    token = response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client
