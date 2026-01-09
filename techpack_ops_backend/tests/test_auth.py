import typing
import pytest
from httpx import AsyncClient
from tests.conftest import TEST_ADMIN_EMAIL, TEST_USER_EMAIL, TEST_PASSWORD


if typing.TYPE_CHECKING:
    from models.user import User


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Test user registration

    Args:
        client (AsyncClient): _description_
    """

    response = await client.post(
        "/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "strongpassword123",
            "role": "user",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["role"] == "user"
    assert data["is_active"] == True
    assert "password" not in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_admin(client: AsyncClient):
    response = await client.post(
        "/auth/register",
        json={
            "email": "newadmin@example.com",
            "password": "strongpassword123",
            "role": "admin",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newadmin@example.com"
    assert data["role"] == "admin"
    assert "password" not in data
    assert "password_hash" not in data


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "email,password",
    [
        (TEST_USER_EMAIL, TEST_PASSWORD),
        (TEST_ADMIN_EMAIL, TEST_PASSWORD),
    ],
)
async def test_login_success_happy_path(
    client: AsyncClient,
    test_user: "User",
    test_admin: "User",
    email: str,
    password: str,
):
    response = await client.post(
        "/auth/jwt/login",
        data={
            "username": email,
            "password": password,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert "access_token" in data


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "email,password",
    [
        (TEST_USER_EMAIL + "1", TEST_PASSWORD),
        (TEST_ADMIN_EMAIL + "2", TEST_PASSWORD),
        (TEST_USER_EMAIL, TEST_PASSWORD + "1"),
        ("someuser@example.com", TEST_PASSWORD),
    ],
)
async def test_login_user_failure_path(
    client: AsyncClient,
    test_user: "User",
    test_admin: "User",
    email: str,
    password: str,
):
    response = await client.post(
        "/auth/jwt/login",
        data={
            "username": email,
            "password": password,
        },
    )

    assert response.status_code == 400
    data = response.json()

    assert data["detail"] == "LOGIN_BAD_CREDENTIALS"
    assert "token_type" not in data
    assert "access_token" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, test_user: "User"):
    response = await client.post(
        "/auth/register", json={"email": test_user.email, "password": "password", "role": "user"}
    )

    assert response.status_code == 400
    assert "REGISTER_USER_ALREADY_EXISTS" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_current_user(authenticated_client: AsyncClient, test_user: "User", db_session):

    response = await authenticated_client.get("/users/me")

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["role"] == test_user.role

@pytest.mark.asyncio
async def test_logout(authenticated_client: AsyncClient):
    response = await authenticated_client.post("/auth/jwt/logout")
    assert response.status_code in (200, 204,)
    