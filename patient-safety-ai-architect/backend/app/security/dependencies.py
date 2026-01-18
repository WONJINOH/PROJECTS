"""
FastAPI Security Dependencies

Authentication and authorization dependencies for endpoints.
"""

from typing import Annotated, Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.models.user import User, Role
from app.security.rbac import Permission, has_permission

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    """
    Get current authenticated user from JWT token.

    Raises:
        HTTPException: If token is invalid or user not found
    """
    # TODO: Implement JWT validation
    # 1. Decode token
    # 2. Validate expiration
    # 3. Get user from database
    # 4. Check if user is active
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication not yet implemented",
        headers={"WWW-Authenticate": "Bearer"},
    )


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
    ) -> None:
        if not has_permission(current_user.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission.value}",
            )

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
    ) -> None:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {', '.join(r.value for r in roles)}",
            )

    return role_checker
