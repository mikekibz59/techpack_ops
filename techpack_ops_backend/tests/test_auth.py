import typing
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.conftest import TEST_ADMIN_EMAIL, TEST_USER_EMAIL, TEST_PASSWORD
from models.user import User
from auth import UserManager
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase


class _TestUserManager(UserManager):
    def __init__(self, user_db):
        super().__init__(user_db)
        self.reset_token = None

    async def on_after_forgot_password(self, user, token, request=None):
        self.reset_token = token


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
    test_user: User,
    test_admin: User,
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
    test_user: User,
    test_admin: User,
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
async def test_register_duplicate_email(client: AsyncClient, test_user: User):
    response = await client.post(
        "/auth/register", json={"email": test_user.email, "password": "password", "role": "user"}
    )

    assert response.status_code == 400
    assert "REGISTER_USER_ALREADY_EXISTS" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_current_user(authenticated_client: AsyncClient, test_user: User, db_session):

    response = await authenticated_client.get("/users/me")

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["role"] == test_user.role


@pytest.mark.asyncio
async def test_logout(authenticated_client: AsyncClient):
    response = await authenticated_client.post("/auth/jwt/logout")
    assert response.status_code in (
        200,
        204,
    )


@pytest.mark.asyncio
async def test_forgot_password_flow(client: AsyncClient, test_user: User, db_session: AsyncSession):
    """Test the complete forgot password flow."""

    # Step 1: Request password reset
    response = await client.post("/auth/forgot-password", json={"email": test_user.email})

    assert response.status_code == 202  # Accepted
    # Note: In real app, email would be sent here
    # For testing, we need to capture the token another way


@pytest.mark.asyncio
async def test_forgot_password_nonexistent_email(client: AsyncClient):
    """Test password reset request for non-existent email."""

    response = await client.post("/auth/forgot-password", json={"email": "doesnotexist@example.com"})

    # Should still return 202 to avoid email enumeration
    assert response.status_code == 202


@pytest.mark.asyncio
async def test_reset_password_with_token(
    client: AsyncClient,
    test_user: User,
    db_session: AsyncSession,
):
    user_db = SQLAlchemyUserDatabase(db_session, User)
    user_manager = _TestUserManager(user_db)

    # Step 1: trigger forgot password
    await user_manager.forgot_password(test_user)

    token = user_manager.reset_token
    assert token is not None

    # Step 2: reset password
    new_password = "newstrongpassword123"
    response = await client.post(
        "/auth/reset-password",
        json={"token": token, "password": new_password},
    )
    assert response.status_code == 200

    # Step 3: verify login
    login_response = await client.post(
        "/auth/jwt/login",
        data={"username": test_user.email, "password": new_password},
    )
    assert login_response.status_code == 200


@pytest.mark.asyncio
async def test_reset_password_invalid_token(client: AsyncClient):
    """Test resetting password with invalid token."""

    response = await client.post(
        "/auth/reset-password", json={"token": "invalid-token-12345", "password": "newpassword123"}
    )

    assert response.status_code == 400
    assert "RESET_PASSWORD_BAD_TOKEN" in response.json()["detail"]


@pytest.mark.asyncio
async def test_complete_password_reset_flow_with_verification(
    client: AsyncClient, test_user: User, db_session: AsyncSession
):
    """Test the complete flow: forget → reset → login with new password."""

    from fastapi_users.password import PasswordHelper

    # Step 1: User forgets password
    response = await client.post("/auth/forgot-password", json={"email": test_user.email})
    assert response.status_code == 202

    # Step 2: Generate token (simulating email click)
    user_db = SQLAlchemyUserDatabase(db_session, User)
    user_manager = _TestUserManager(user_db)
    await user_manager.forgot_password(test_user)

    # Step 3: User resets password
    new_password = "mynewsecurepassword123"
    reset_response = await client.post(
        "/auth/reset-password", json={"token": user_manager.reset_token, "password": new_password}
    )
    assert reset_response.status_code == 200

    # Step 4: Old password should NOT work
    old_login = await client.post(
        "/auth/jwt/login", data={"username": test_user.email, "password": "testpassword"}  # Old password
    )
    assert old_login.status_code == 400

    # Step 5: New password SHOULD work
    new_login = await client.post(
        "/auth/jwt/login", data={"username": test_user.email, "password": new_password}  # New password
    )
    assert new_login.status_code == 200
    assert "access_token" in new_login.json()

    # Step 6: Verify the password was actually changed in DB
    password_helper = PasswordHelper()
    refreshed_user = await db_session.get(User, test_user.id)
    assert password_helper.verify_and_update(new_password, refreshed_user.hashed_password)[0]


@pytest.mark.asyncio
async def test_token_cannot_be_reused(client: AsyncClient, test_user: User, db_session: AsyncSession):
    """Test that reset tokens can only be used once."""

    # Generate token
    user_db = SQLAlchemyUserDatabase(db_session, User)
    user_manager = _TestUserManager(user_db)
    await user_manager.forgot_password(test_user)

    # Use token once - should work
    first_reset = await client.post(
        "/auth/reset-password", json={"token": user_manager.reset_token, "password": "firstnewpassword123"}
    )
    assert first_reset.status_code == 200

    # Try to use same token again - should fail
    second_reset = await client.post(
        "/auth/reset-password", json={"token": user_manager.reset_token, "password": "secondnewpassword123"}
    )
    assert second_reset.status_code == 400
