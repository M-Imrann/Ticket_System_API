from sqlalchemy import (
    Column, Integer, String, ForeignKey,
    Text, Enum as SqlEnum, DateTime, func
)
from sqlalchemy.orm import relationship
from .database import Base
from .schemas import UserRole, TicketStatus


class User(Base):
    """
    SQLAlchemy model for the User table.
    """
    __tablename__ = "users"

    # Unique user ID
    id = Column(Integer, primary_key=True, index=True)
    # User email
    email = Column(String, unique=True, index=True, nullable=False)
    # Hashed password
    hashed_password = Column(String, nullable=False)
    # User role
    role = Column(SqlEnum(UserRole), nullable=False)


class Ticket(Base):
    """
    SQLAlchemy model for the Ticket table.
    """
    __tablename__ = "tickets"

    # Unique ticket ID
    id = Column(Integer, primary_key=True, index=True)
    # Ticket title
    title = Column(String, index=True, nullable=False)
    # Optional ticket description
    description = Column(Text, nullable=True)
    # Ticket status (enum)
    status = Column(
        SqlEnum(TicketStatus),
        nullable=False,
        default=TicketStatus.open
    )
    # Creation timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # User who created ticket
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Reference to creator user
    creator = relationship("User")
    # List of replies to this ticket
    replies = relationship(
        "Reply",
        back_populates="ticket",
        cascade="all, delete-orphan"
    )


class Reply(Base):
    """
    SQLAlchemy model for the Reply table.
    """
    __tablename__ = "replies"

    # Unique reply ID
    id = Column(Integer, primary_key=True, index=True)
    # Related ticket ID
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    # Reply message content
    message = Column(Text, nullable=False)
    # Reply timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # User who replied
    replied_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Reference to ticket
    ticket = relationship("Ticket", back_populates="replies")
    # Reference to replier user
    replier = relationship("User")
