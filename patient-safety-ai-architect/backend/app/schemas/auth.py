"""
Authentication Schemas (Pydantic)
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field

from app.models.user import Role


class Token(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """JWT token payload."""

    sub: int  # user_id
    role: str
    exp: int


class UserCreate(BaseModel):
    """Schema for creating a user."""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=2, max_length=100)
    role: Role = Role.REPORTER
    department: Optional[str] = Field(None, max_length=100)


class UserResponse(BaseModel):
    """Schema for user response."""

    id: int
    username: str
    email: str
    full_name: str
    role: Role
    department: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True
