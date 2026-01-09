from fastapi_users import schemas


class UserRead(schemas.BaseUser[int]):
    """Schema for reading user data."""

    role: str


class UserCreate(schemas.BaseUserCreate):
    """Schema for creating a user."""

    role: str = "user"


class UserUpdate(schemas.BaseUserUpdate):
    """Schema for updating a user."""

    role: str = None
