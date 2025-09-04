import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from . import models, database, schemas

SECRET_KEY = os.getenv("SECRET_KEY", "secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt.

    Args:
        password: The plain text password to hash.

    Returns:
        str: The hashed password.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password.

    Args:
        plain_password: The plain text password to verify.
        hashed_password: The hashed password to compare against.

    Returns:
        bool: True if the password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict,
    expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES
) -> str:
    """
    Create a JWT access token with expiration.

    Args:
        data: Dictionary containing token claims.
        expires_minutes: Token expiration time in minutes.

    Returns:
        str: Encoded JWT token string.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str
) -> Optional[models.User]:
    """
    Authenticate a user by email and password.

    Args:
        db: Async SQLAlchemy session.
        email: User email address.
        password: Plain text password.

    Returns:
        Optional[models.User]:
            User object if authentication successful, None otherwise.
    """
    user_query = await db.execute(
        select(models.User).where(models.User.email == email)
    )
    user = user_query.scalars().first()
    # Return None if user not found or password is incorrect
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(database.get_db),
) -> models.User:
    """
    Get current authenticated user from JWT token.

    Args:
        token: JWT token from Authorization header.
        db: Async SQLAlchemy session.

    Returns:
        models.User: Authenticated user object.

    Raises:
        HTTPException: If token is invalid or user not found.
    """
    # Return None if token is invalid or user not found
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        token_data = schemas.TokenData(sub=email)
    except JWTError:
        return None

    user_query = await db.execute(
        select(models.User).where(models.User.email == token_data.sub)
    )
    user = user_query.scalars().first()
    if user is None:
        return None
    return user


async def validate_websocket_token(
    token: str,
    db: AsyncSession
) -> models.User:
    """
    Validate token for WebSocket connections.

    Args:
        token: JWT token from query parameter.
        db: Async SQLAlchemy session.

    Returns:
        models.User: Authenticated user object.

    Raises:
        HTTPException: If token is invalid or user not found.
    """
    # Returns None if token is invalid or user not found
    return await get_current_user(token, db)
