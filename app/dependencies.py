from fastapi import Depends, HTTPException, status
from .auth import get_current_user
from .models import User
from .schemas import UserRole


async def require_user(user: User = Depends(get_current_user)) -> User:
    """
    Async dependency to ensure the current user has the 'user' role.

    Raises HTTPException if not.
    """
    if user.role != UserRole.user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Users only."
        )
    return user


async def require_agent(user: User = Depends(get_current_user)) -> User:
    """
    Async dependency to ensure the current user has the 'agent' role.

    Raises HTTPException if not.
    """
    if user.role != UserRole.agent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Agents only."
        )
    return user
