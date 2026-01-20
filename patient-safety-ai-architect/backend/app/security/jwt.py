"""
JWT Token Utilities

JWT creation and validation for authentication.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt

from app.config import settings
from app.schemas.auth import TokenPayload


def create_access_token(
    user_id: int,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        user_id: User ID to encode in token
        role: User role to encode in token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT string
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }

    encoded_jwt = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[TokenPayload]:
    """
    Decode and validate a JWT access token.

    Args:
        token: JWT token string

    Returns:
        TokenPayload if valid, None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        user_id = payload.get("sub")
        role = payload.get("role")
        exp = payload.get("exp")

        if user_id is None or role is None:
            return None

        return TokenPayload(
            sub=int(user_id),
            role=role,
            exp=exp,
        )
    except JWTError:
        return None


def verify_token(token: str) -> bool:
    """
    Verify if a token is valid (not expired, properly signed).

    Args:
        token: JWT token string

    Returns:
        True if valid, False otherwise
    """
    return decode_access_token(token) is not None
