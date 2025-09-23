from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app import models, schemas


async def create_user(
    db: AsyncSession,
    email: str,
    hashed_password: str,
    role: schemas.UserRole
) -> models.User:
    """
    Create a new user in the database.

    Args:
        db: Database session.
        email: User's email address.
        hashed_password: User's hashed password.
        role: User's role.

    Returns:
        The created user object.
    """
    # Create and add new user to the database
    user = models.User(email=email, hashed_password=hashed_password, role=role)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_user_by_email(
    db: AsyncSession,
    email: str
) -> Optional[models.User]:
    """
    Fetch a user by their email address.

    Args:
        db: Database session.
        email: User's email address.

    Returns:
        The user object if found, otherwise raises HTTPException.
    """
    # Query user by email
    query = select(models.User).where(models.User.email == email)
    query_result = await db.execute(query)
    user = query_result.scalars().first()
    return user
