"""
FastAPI Security Dependencies

Authentication and authorization dependencies for endpoints.
"""

from typing import Annotated, Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, Role
from app.security.rbac import Permission, has_permission
from app.security.jwt import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Get current authenticated user from JWT token.

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Decode and validate token
    token_data = decode_access_token(token)
    if token_data is None:
        raise credentials_exception

    # Get user from database
    result = await db.execute(
        select(User).where(User.id == token_data.sub)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Get current user and verify they are active.

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    return current_user


def require_permission(permission: Permission) -> Callable:
    """
    Dependency factory for permission checking.

    Usage:
        @router.get("/incidents")
        async def list_incidents(
            _: Annotated[None, Depends(require_permission(Permission.VIEW_INCIDENT))]
        ):
            ...
    """

    async def permission_checker(
        current_user: Annotated[User, Depends(get_current_active_user)],
    ) -> User:
        if not has_permission(current_user.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission.value}",
            )
        return current_user

    return permission_checker


def require_role(*roles: Role) -> Callable:
    """
    Dependency factory for role checking.

    Usage:
        @router.post("/admin/users")
        async def create_user(
            _: Annotated[None, Depends(require_role(Role.ADMIN))]
        ):
            ...
    """

    async def role_checker(
        current_user: Annotated[User, Depends(get_current_active_user)],
    ) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {', '.join(r.value for r in roles)}",
            )
        return current_user

    return role_checker


# Optional auth dependency - returns None if not authenticated
async def get_optional_user(
    token: Annotated[str | None, Depends(OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User | None:
    """
    Get current user if authenticated, None otherwise.

    Useful for endpoints that work both authenticated and unauthenticated.
    """
    if token is None:
        return None

    token_data = decode_access_token(token)
    if token_data is None:
        return None

    result = await db.execute(
        select(User).where(User.id == token_data.sub)
    )
    return result.scalar_one_or_none()
