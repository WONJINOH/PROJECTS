"""
Authentication Schemas (Pydantic)
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import Role, UserStatus


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
    """Schema for creating a user (by admin)."""

    username: str = Field(..., min_length=3, max_length=50, description="사원번호")
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=2, max_length=100)
    role: Role = Role.REPORTER
    department: Optional[str] = Field(None, max_length=100)


class UserRegisterRequest(BaseModel):
    """Schema for user self-registration (pending approval)."""

    username: str = Field(..., min_length=3, max_length=50, description="사원번호")
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=2, max_length=100)
    department: Optional[str] = Field(None, max_length=100)


class UserApprovalAction(BaseModel):
    """Schema for approving/rejecting user registration."""

    action: str = Field(..., pattern="^(approve|reject)$")
    role: Optional[Role] = Field(None, description="Assign role when approving")
    rejection_reason: Optional[str] = Field(None, max_length=500)


class UserResponse(BaseModel):
    """Schema for user response."""

    id: int
    username: str
    email: str
    full_name: str
    role: Role
    department: Optional[str]
    is_active: bool
    status: UserStatus
    password_expires_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    created_at: datetime
    approved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    """Schema for user list response."""

    items: list[UserResponse]
    total: int
    skip: int
    limit: int


class PasswordChangeRequest(BaseModel):
    """Schema for password change."""

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=100)


class UserUpdateRequest(BaseModel):
    """Schema for updating user profile (Admin only)."""

    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    department: Optional[str] = Field(None, max_length=100)


class UserSuspendRequest(BaseModel):
    """Schema for suspending a user."""

    reason: Optional[str] = Field(None, max_length=500)
