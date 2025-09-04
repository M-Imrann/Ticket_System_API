from pydantic import BaseModel, EmailStr
from typing import Optional, List
from enum import Enum


class UserRole(str, Enum):
    """
    Enum for user roles in the system.
    """
    user = "user"
    agent = "agent"


class TicketStatus(str, Enum):
    """
    Enum for ticket status values.
    """
    open = "open"
    in_review = "in_review"
    close = "close"


class Token(BaseModel):
    """
    Schema for JWT access token response.
    """
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """
    Schema for token payload data.
    """
    sub: Optional[str] = None


class UserCreate(BaseModel):
    """
    Schema for user registration input.
    """
    email: EmailStr
    password: str
    role: UserRole = UserRole.user


class UserRead(BaseModel):
    """
    Schema for user data output.
    """
    id: int
    email: EmailStr
    role: UserRole

    class Config:
        from_attributes = True


class TicketCreate(BaseModel):
    """
    Schema for ticket creation input.
    """
    title: str
    description: Optional[str] = None


class TicketRead(BaseModel):
    """
    Schema for ticket data output.
    """
    id: int
    title: str
    description: Optional[str]
    status: TicketStatus
    created_by: int

    class Config:
        from_attributes = True


class ReplyCreate(BaseModel):
    """
    Schema for reply creation input.
    """
    message: str


class ReplyRead(BaseModel):
    """
    Schema for reply data output.
    """
    id: int
    message: str
    replied_by: int

    class Config:
        from_attributes = True


class TicketDetail(BaseModel):
    """
    Schema for detailed ticket output including replies.
    """
    ticket: TicketRead
    replies: List[ReplyRead]


class TicketStatusUpdate(BaseModel):
    """
    Schema for updating ticket status.
    """
    status: TicketStatus
