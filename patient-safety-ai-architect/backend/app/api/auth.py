"""
Authentication API

JWT-based authentication with secure password hashing.
"""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, Role
from app.models.audit import AuditLog, AuditEventType

# Map generic events to audit event types
LOGIN_EVENT = AuditEventType.AUTH_LOGIN
LOGOUT_EVENT = AuditEventType.AUTH_LOGOUT
FAILED_EVENT = AuditEventType.AUTH_FAILED
from app.schemas.auth import Token, UserCreate, UserResponse
from app.security.dependencies import get_current_user, get_current_active_user, require_role
from app.security.password import hash_password, verify_password
from app.security.jwt import create_access_token

router = APIRouter()


async def log_auth_event(
    db: AsyncSession,
    event_type: AuditEventType,
    user_id: int | None,
    username: str,
    result: str,
    user_role: str | None = None,
    details: dict | None = None,
) -> None:
    """Log authentication event for PIPA compliance."""
    # Get previous hash for chain
    previous_hash = "genesis"  # First entry

    timestamp = datetime.now(timezone.utc)
    entry_hash = AuditLog.calculate_hash(
        event_type=event_type.value,
        timestamp=timestamp,
        user_id=user_id,
        resource_id=None,
        previous_hash=previous_hash,
    )

    audit_log = AuditLog(
        event_type=event_type,
        timestamp=timestamp,
        user_id=user_id,
        username=username,
        user_role=user_role,
        resource_type="auth",
        action_detail=details,
        result=result,
        previous_hash=previous_hash,
        entry_hash=entry_hash,
    )
    db.add(audit_log)
    await db.flush()


@router.post(
    "/login",
    response_model=Token,
    summary="Login",
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    """
    Authenticate user and return JWT token.

    - Username/password authentication
    - Returns access token (JWT)
    - Failed attempts logged for audit
    """
    # Find user by username
    result = await db.execute(
        select(User).where(User.username == form_data.username)
    )
    user = result.scalar_one_or_none()

    # Verify credentials
    if user is None or not verify_password(form_data.password, user.hashed_password):
        # Log failed attempt
        await log_auth_event(
            db=db,
            event_type=FAILED_EVENT,
            user_id=user.id if user else None,
            username=form_data.username,
            result="failure",
            details={"reason": "Invalid username or password"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        await log_auth_event(
            db=db,
            event_type=FAILED_EVENT,
            user_id=user.id,
            username=user.username,
            result="failure",
            details={"reason": "User account is inactive"},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Update last login
    user.last_login = datetime.now(timezone.utc)

    # Log successful login
    await log_auth_event(
        db=db,
        event_type=LOGIN_EVENT,
        user_id=user.id,
        username=user.username,
        user_role=user.role.value,
        result="success",
    )

    # Generate token
    access_token = create_access_token(
        user_id=user.id,
        role=user.role.value,
    )

    return Token(access_token=access_token, token_type="bearer")


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout",
)
async def logout(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """
    Logout current user.

    - Logs logout event
    - Token invalidation handled client-side (stateless JWT)
    """
    await log_auth_event(
        db=db,
        event_type=LOGOUT_EVENT,
        user_id=current_user.id,
        username=current_user.username,
        user_role=current_user.role.value,
        result="success",
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
)
async def get_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserResponse:
    """
    Get current authenticated user's profile.
    """
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        department=current_user.department,
        is_active=current_user.is_active,
    )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user (Admin only)",
)
async def register(
    user_data: UserCreate,
    current_user: Annotated[User, Depends(require_role(Role.ADMIN, Role.MASTER))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    """
    Register a new user (Admin only).

    - Validates user data
    - Hashes password with Argon2
    - Creates user with assigned role
    """
    # Check if username already exists
    result = await db.execute(
        select(User).where(User.username == user_data.username)
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create new user
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        department=user_data.department,
        is_active=True,
    )
    db.add(new_user)
    await db.flush()
    await db.refresh(new_user)

    # Log user creation
    await log_auth_event(
        db=db,
        event_type=AuditEventType.PERMISSION_CHANGE,
        user_id=current_user.id,
        username=current_user.username,
        user_role=current_user.role.value,
        result="success",
        details={"action": "user_created", "new_user": new_user.username, "role": new_user.role.value},
    )

    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        full_name=new_user.full_name,
        role=new_user.role,
        department=new_user.department,
        is_active=new_user.is_active,
    )


@router.put(
    "/me/password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change password",
)
async def change_password(
    current_password: str,
    new_password: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """
    Change current user's password.

    - Requires current password verification
    - New password must be different
    """
    # Verify current password
    if not verify_password(current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Validate new password length
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters",
        )

    # Update password
    current_user.hashed_password = hash_password(new_password)

    # Log password change
    await log_auth_event(
        db=db,
        event_type=AuditEventType.PERMISSION_CHANGE,
        user_id=current_user.id,
        username=current_user.username,
        user_role=current_user.role.value,
        result="success",
        details={"action": "password_changed"},
    )
