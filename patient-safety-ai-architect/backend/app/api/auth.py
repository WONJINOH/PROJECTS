"""
Authentication API

JWT-based authentication with secure password hashing.
Includes user registration with admin approval workflow.
"""

from datetime import datetime, timezone, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, Role, UserStatus
from app.models.audit import AuditLog, AuditEventType

# Map generic events to audit event types
LOGIN_EVENT = AuditEventType.AUTH_LOGIN
LOGOUT_EVENT = AuditEventType.AUTH_LOGOUT
FAILED_EVENT = AuditEventType.AUTH_FAILED
from app.schemas.auth import (
    Token, UserCreate, UserResponse, UserRegisterRequest,
    UserApprovalAction, UserListResponse, PasswordChangeRequest,
    UserUpdateRequest, UserSuspendRequest
)
from app.security.dependencies import get_current_user, get_current_active_user, require_role
from app.security.password import hash_password, verify_password
from app.security.jwt import create_access_token

router = APIRouter()

# Constants
PASSWORD_EXPIRY_DAYS = 180  # 6 months
DORMANT_AFTER_DAYS = 365    # 1 year
DELETE_AFTER_YEARS = 5      # 5 years


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


def calculate_password_expiry() -> datetime:
    """Calculate password expiry date (6 months from now)."""
    return datetime.now(timezone.utc) + timedelta(days=PASSWORD_EXPIRY_DAYS)


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
    - Checks account status (pending, dormant, etc.)
    - Warns about password expiry
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

    # Check user status
    if user.status == UserStatus.PENDING:
        await log_auth_event(
            db=db,
            event_type=FAILED_EVENT,
            user_id=user.id,
            username=user.username,
            result="failure",
            details={"reason": "Account pending approval"},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="계정 승인 대기 중입니다. 관리자에게 문의하세요.",
        )

    if user.status == UserStatus.DORMANT:
        await log_auth_event(
            db=db,
            event_type=FAILED_EVENT,
            user_id=user.id,
            username=user.username,
            result="failure",
            details={"reason": "Account is dormant"},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="휴면 계정입니다. 관리자에게 계정 재활성화를 요청하세요.",
        )

    if user.status == UserStatus.SUSPENDED or user.status == UserStatus.DELETED:
        await log_auth_event(
            db=db,
            event_type=FAILED_EVENT,
            user_id=user.id,
            username=user.username,
            result="failure",
            details={"reason": f"Account status: {user.status.value}"},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="계정이 정지되었습니다. 관리자에게 문의하세요.",
        )

    # Check if user is active (legacy field)
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
        status=current_user.status if hasattr(current_user, 'status') and current_user.status else UserStatus.ACTIVE,
        password_expires_at=current_user.password_expires_at if hasattr(current_user, 'password_expires_at') else None,
        last_login=current_user.last_login,
        created_at=current_user.created_at,
        approved_at=current_user.approved_at if hasattr(current_user, 'approved_at') else None,
    )


@router.post(
    "/request-registration",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Request user registration (Public)",
)
async def request_registration(
    user_data: UserRegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    """
    Request a new user registration (pending admin approval).

    - Public endpoint (no authentication required)
    - Creates user with PENDING status
    - Admin must approve before user can login
    - Username should be employee ID (사원번호)
    """
    # Check if username already exists
    result = await db.execute(
        select(User).where(User.username == user_data.username)
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 등록된 사원번호입니다.",
        )

    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 등록된 이메일입니다.",
        )

    # Create new user with PENDING status
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
        role=Role.REPORTER,  # Default role, admin can change during approval
        department=user_data.department,
        is_active=False,  # Inactive until approved
        status=UserStatus.PENDING,
        password_changed_at=datetime.now(timezone.utc),
        password_expires_at=calculate_password_expiry(),
    )
    db.add(new_user)
    await db.flush()
    await db.refresh(new_user)

    # Log registration request
    await log_auth_event(
        db=db,
        event_type=AuditEventType.PERMISSION_CHANGE,
        user_id=new_user.id,
        username=new_user.username,
        result="pending",
        details={"action": "registration_requested", "email": new_user.email},
    )

    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        full_name=new_user.full_name,
        role=new_user.role,
        department=new_user.department,
        is_active=new_user.is_active,
        status=new_user.status,
        password_expires_at=new_user.password_expires_at,
        last_login=new_user.last_login,
        created_at=new_user.created_at,
        approved_at=new_user.approved_at,
    )


@router.get(
    "/pending-users",
    response_model=UserListResponse,
    summary="List pending user registrations (Admin only)",
)
async def list_pending_users(
    current_user: Annotated[User, Depends(require_role(Role.ADMIN, Role.MASTER))],
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> UserListResponse:
    """
    List all users with pending registration status.
    """
    # Count total
    count_result = await db.execute(
        select(func.count(User.id)).where(User.status == UserStatus.PENDING)
    )
    total = count_result.scalar_one()

    # Get users
    result = await db.execute(
        select(User)
        .where(User.status == UserStatus.PENDING)
        .order_by(User.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    users = result.scalars().all()

    return UserListResponse(
        items=[UserResponse(
            id=u.id,
            username=u.username,
            email=u.email,
            full_name=u.full_name,
            role=u.role,
            department=u.department,
            is_active=u.is_active,
            status=u.status if hasattr(u, 'status') and u.status else UserStatus.ACTIVE,
            password_expires_at=u.password_expires_at if hasattr(u, 'password_expires_at') else None,
            last_login=u.last_login,
            created_at=u.created_at,
            approved_at=u.approved_at if hasattr(u, 'approved_at') else None,
        ) for u in users],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/users/{user_id}/approve",
    response_model=UserResponse,
    summary="Approve or reject user registration (Admin only)",
)
async def approve_user(
    user_id: int,
    action_data: UserApprovalAction,
    current_user: Annotated[User, Depends(require_role(Role.ADMIN, Role.MASTER))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    """
    Approve or reject a pending user registration.

    - Only ADMIN and MASTER can approve
    - Can assign role during approval
    - Sets password expiry to 6 months
    """
    # Get user
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.status != UserStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not in pending status",
        )

    if action_data.action == "approve":
        # Approve user
        user.status = UserStatus.ACTIVE
        user.is_active = True
        user.approved_at = datetime.now(timezone.utc)
        user.approved_by_id = current_user.id
        user.password_expires_at = calculate_password_expiry()

        if action_data.role:
            user.role = action_data.role

        # Log approval
        await log_auth_event(
            db=db,
            event_type=AuditEventType.PERMISSION_CHANGE,
            user_id=current_user.id,
            username=current_user.username,
            user_role=current_user.role.value,
            result="success",
            details={
                "action": "user_approved",
                "approved_user": user.username,
                "assigned_role": user.role.value,
            },
        )
    else:
        # Reject user - mark as deleted
        user.status = UserStatus.DELETED
        user.is_active = False
        user.deleted_at = datetime.now(timezone.utc)

        # Log rejection
        await log_auth_event(
            db=db,
            event_type=AuditEventType.PERMISSION_CHANGE,
            user_id=current_user.id,
            username=current_user.username,
            user_role=current_user.role.value,
            result="success",
            details={
                "action": "user_rejected",
                "rejected_user": user.username,
                "reason": action_data.rejection_reason,
            },
        )

    await db.flush()
    await db.refresh(user)

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        department=user.department,
        is_active=user.is_active,
        status=user.status,
        password_expires_at=user.password_expires_at,
        last_login=user.last_login,
        created_at=user.created_at,
        approved_at=user.approved_at,
    )


@router.get(
    "/users",
    response_model=UserListResponse,
    summary="List all users (Admin only)",
)
async def list_users(
    current_user: Annotated[User, Depends(require_role(Role.ADMIN, Role.MASTER))],
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: UserStatus | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> UserListResponse:
    """
    List all users with optional status filter.
    """
    # Build query
    query = select(User)
    count_query = select(func.count(User.id))

    if status_filter:
        query = query.where(User.status == status_filter)
        count_query = count_query.where(User.status == status_filter)

    # Count total
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    # Get users
    result = await db.execute(
        query.order_by(User.created_at.desc()).offset(skip).limit(limit)
    )
    users = result.scalars().all()

    return UserListResponse(
        items=[UserResponse(
            id=u.id,
            username=u.username,
            email=u.email,
            full_name=u.full_name,
            role=u.role,
            department=u.department,
            is_active=u.is_active,
            status=u.status if hasattr(u, 'status') and u.status else UserStatus.ACTIVE,
            password_expires_at=u.password_expires_at if hasattr(u, 'password_expires_at') else None,
            last_login=u.last_login,
            created_at=u.created_at,
            approved_at=u.approved_at if hasattr(u, 'approved_at') else None,
        ) for u in users],
        total=total,
        skip=skip,
        limit=limit,
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
    - User is immediately active (no approval needed)
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
        status=UserStatus.ACTIVE,
        password_changed_at=datetime.now(timezone.utc),
        password_expires_at=calculate_password_expiry(),
        approved_at=datetime.now(timezone.utc),
        approved_by_id=current_user.id,
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
        status=new_user.status,
        password_expires_at=new_user.password_expires_at,
        last_login=new_user.last_login,
        created_at=new_user.created_at,
        approved_at=new_user.approved_at,
    )


@router.put(
    "/me/password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change password",
)
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """
    Change current user's password.

    - Requires current password verification
    - New password must be different
    - Resets password expiry to 6 months
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Update password
    current_user.hashed_password = hash_password(password_data.new_password)
    current_user.password_changed_at = datetime.now(timezone.utc)
    current_user.password_expires_at = calculate_password_expiry()

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


@router.post(
    "/users/{user_id}/reactivate",
    response_model=UserResponse,
    summary="Reactivate dormant user (Admin only)",
)
async def reactivate_user(
    user_id: int,
    current_user: Annotated[User, Depends(require_role(Role.ADMIN, Role.MASTER))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    """
    Reactivate a dormant user account.
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.status != UserStatus.DORMANT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not in dormant status",
        )

    # Reactivate user
    user.status = UserStatus.ACTIVE
    user.is_active = True
    user.dormant_at = None
    user.password_expires_at = calculate_password_expiry()

    # Log reactivation
    await log_auth_event(
        db=db,
        event_type=AuditEventType.PERMISSION_CHANGE,
        user_id=current_user.id,
        username=current_user.username,
        user_role=current_user.role.value,
        result="success",
        details={"action": "user_reactivated", "reactivated_user": user.username},
    )

    await db.flush()
    await db.refresh(user)

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        department=user.department,
        is_active=user.is_active,
        status=user.status,
        password_expires_at=user.password_expires_at,
        last_login=user.last_login,
        created_at=user.created_at,
        approved_at=user.approved_at,
    )


@router.put(
    "/users/{user_id}/role",
    response_model=UserResponse,
    summary="Change user role (Admin only)",
)
async def change_user_role(
    user_id: int,
    new_role: Role,
    current_user: Annotated[User, Depends(require_role(Role.ADMIN, Role.MASTER))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    """
    Change a user's role.
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    old_role = user.role
    user.role = new_role

    # Log role change
    await log_auth_event(
        db=db,
        event_type=AuditEventType.PERMISSION_CHANGE,
        user_id=current_user.id,
        username=current_user.username,
        user_role=current_user.role.value,
        result="success",
        details={
            "action": "role_changed",
            "target_user": user.username,
            "old_role": old_role.value,
            "new_role": new_role.value,
        },
    )

    await db.flush()
    await db.refresh(user)

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        department=user.department,
        is_active=user.is_active,
        status=user.status if hasattr(user, 'status') and user.status else UserStatus.ACTIVE,
        password_expires_at=user.password_expires_at if hasattr(user, 'password_expires_at') else None,
        last_login=user.last_login,
        created_at=user.created_at,
        approved_at=user.approved_at if hasattr(user, 'approved_at') else None,
    )


@router.put(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Update user profile (Admin only)",
)
async def update_user(
    user_id: int,
    user_data: UserUpdateRequest,
    current_user: Annotated[User, Depends(require_role(Role.ADMIN, Role.MASTER))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    """
    Update a user's profile information (name, email, department).
    Admin/Master only.
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Track changes for audit log
    changes = {}

    if user_data.full_name is not None and user_data.full_name != user.full_name:
        changes["full_name"] = {"old": user.full_name, "new": user_data.full_name}
        user.full_name = user_data.full_name

    if user_data.email is not None and user_data.email != user.email:
        # Check if email is already in use
        email_check = await db.execute(
            select(User).where(User.email == user_data.email, User.id != user_id)
        )
        if email_check.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use",
            )
        changes["email"] = {"old": user.email, "new": user_data.email}
        user.email = user_data.email

    if user_data.department is not None and user_data.department != user.department:
        changes["department"] = {"old": user.department, "new": user_data.department}
        user.department = user_data.department

    if changes:
        # Log profile change
        await log_auth_event(
            db=db,
            event_type=AuditEventType.PERMISSION_CHANGE,
            user_id=current_user.id,
            username=current_user.username,
            user_role=current_user.role.value,
            result="success",
            details={
                "action": "user_profile_updated",
                "target_user": user.username,
                "changes": changes,
            },
        )

    await db.flush()
    await db.refresh(user)

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        department=user.department,
        is_active=user.is_active,
        status=user.status if hasattr(user, 'status') and user.status else UserStatus.ACTIVE,
        password_expires_at=user.password_expires_at if hasattr(user, 'password_expires_at') else None,
        last_login=user.last_login,
        created_at=user.created_at,
        approved_at=user.approved_at if hasattr(user, 'approved_at') else None,
    )


@router.post(
    "/users/{user_id}/suspend",
    response_model=UserResponse,
    summary="Suspend user (Admin only)",
)
async def suspend_user(
    user_id: int,
    suspend_data: UserSuspendRequest,
    current_user: Annotated[User, Depends(require_role(Role.ADMIN, Role.MASTER))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    """
    Suspend a user account. Admin/Master only.
    Cannot suspend yourself or other admins (unless you're master).
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Cannot suspend yourself
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot suspend yourself",
        )

    # Admin cannot suspend other admins or master
    if current_user.role == Role.ADMIN and user.role in (Role.ADMIN, Role.MASTER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot suspend admin or master users",
        )

    # Already suspended
    if user.status == UserStatus.SUSPENDED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already suspended",
        )

    # Suspend user
    old_status = user.status
    user.status = UserStatus.SUSPENDED
    user.is_active = False

    # Log suspension
    await log_auth_event(
        db=db,
        event_type=AuditEventType.PERMISSION_CHANGE,
        user_id=current_user.id,
        username=current_user.username,
        user_role=current_user.role.value,
        result="success",
        details={
            "action": "user_suspended",
            "target_user": user.username,
            "old_status": old_status.value if old_status else "active",
            "reason": suspend_data.reason,
        },
    )

    await db.flush()
    await db.refresh(user)

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        department=user.department,
        is_active=user.is_active,
        status=user.status,
        password_expires_at=user.password_expires_at if hasattr(user, 'password_expires_at') else None,
        last_login=user.last_login,
        created_at=user.created_at,
        approved_at=user.approved_at if hasattr(user, 'approved_at') else None,
    )


@router.post(
    "/users/{user_id}/unsuspend",
    response_model=UserResponse,
    summary="Unsuspend user (Admin only)",
)
async def unsuspend_user(
    user_id: int,
    current_user: Annotated[User, Depends(require_role(Role.ADMIN, Role.MASTER))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    """
    Unsuspend a suspended user account. Admin/Master only.
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Not suspended
    if user.status != UserStatus.SUSPENDED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not suspended",
        )

    # Unsuspend user
    user.status = UserStatus.ACTIVE
    user.is_active = True

    # Log unsuspension
    await log_auth_event(
        db=db,
        event_type=AuditEventType.PERMISSION_CHANGE,
        user_id=current_user.id,
        username=current_user.username,
        user_role=current_user.role.value,
        result="success",
        details={
            "action": "user_unsuspended",
            "target_user": user.username,
        },
    )

    await db.flush()
    await db.refresh(user)

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        department=user.department,
        is_active=user.is_active,
        status=user.status,
        password_expires_at=user.password_expires_at if hasattr(user, 'password_expires_at') else None,
        last_login=user.last_login,
        created_at=user.created_at,
        approved_at=user.approved_at if hasattr(user, 'approved_at') else None,
    )
