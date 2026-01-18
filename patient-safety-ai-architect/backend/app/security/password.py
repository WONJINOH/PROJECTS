"""
Password Hashing

Uses Argon2 (recommended) with bcrypt fallback.
PIPA Art. 29 compliant password protection.
"""

from passlib.context import CryptContext

# Argon2 is recommended, bcrypt as fallback
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto",
    argon2__rounds=4,  # Adjust based on performance
    argon2__memory_cost=65536,  # 64MB
    argon2__parallelism=2,
    bcrypt__rounds=12,
)


def hash_password(password: str) -> str:
    """
    Hash a password using Argon2.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored hash to verify against

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)
