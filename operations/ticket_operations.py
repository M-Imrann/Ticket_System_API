
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app import models, schemas
from sqlalchemy.orm import joinedload


async def create_ticket(
    db: AsyncSession,
    title: str,
    description: str | None,
    created_by: int
) -> models.Ticket:
    """
    Create a new ticket in the database.

    Args:
        db: SQLAlchemy async session.
        title: Title of the ticket.
        description: Description of the ticket.
        created_by: User ID who created the ticket.

    Returns:
        models.Ticket: The created ticket object.
    """
    ticket = models.Ticket(
        title=title,
        description=description,
        created_by=created_by
    )
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)
    return ticket


async def get_ticket(
    db: AsyncSession,
    ticket_id: int
) -> Optional[models.Ticket]:
    """
    Retrieve a ticket by its ID, eagerly loading replies and creator.

    Args:
        db: SQLAlchemy async session.
        ticket_id: Ticket ID to retrieve.

    Returns:
        Optional[models.Ticket]: The ticket object or None if not found.
    """
    ticket = await db.execute(
        select(models.Ticket)
        .options(
            joinedload(models.Ticket.replies),
            joinedload(models.Ticket.creator)
            # Preload creator for API response
        )
        .where(models.Ticket.id == ticket_id)
    )
    return ticket.scalars().first()


async def add_reply(
    db: AsyncSession,
    ticket_id: int,
    message: str,
    replied_by: int
) -> Optional[models.Reply]:
    """
    Add a reply to a ticket.

    Args:
        db: SQLAlchemy async session.
        ticket_id: Ticket ID to reply to.
        message: Reply message.
        replied_by: User ID of the replier.

    Returns:
        Optional[models.Reply]: The created reply or None if ticket not found.
    """
    result = await db.execute(
        select(models.Ticket).where(models.Ticket.id == ticket_id)
    )
    ticket = result.scalars().first()
    if not ticket:
        return None
    reply = models.Reply(
        ticket_id=ticket_id,
        message=message,
        replied_by=replied_by
    )
    db.add(reply)
    await db.commit()
    await db.refresh(reply)
    return reply


async def change_ticket_status(
    db: AsyncSession,
    ticket: models.Ticket,
    ticket_status: schemas.TicketStatus
) -> Optional[models.Ticket]:
    """
    Change the status of a ticket.

    Args:
        db: SQLAlchemy async session.
        ticket: Ticket object to update.
        ticket_status: New status value.

    Returns:
        Optional[models.Ticket]: Updated ticket or None if not found.
    """
    ticket.status = ticket_status
    await db.commit()
    await db.refresh(ticket)
    return ticket


async def get_ticket_with_replies(
    db: AsyncSession,
    ticket_id: int
) -> Optional[tuple[models.Ticket, list[models.Reply]]]:
    """
    Retrieve a ticket and its associated replies as a tuple.

    Args:
        db: SQLAlchemy async session.
        ticket_id: Ticket ID to retrieve.

    Returns:
        Optional[tuple[models.Ticket, list[models.Reply]]]:
            Tuple of ticket and its replies, or None if not found.
    """
    ticket = await get_ticket(db, ticket_id)
    if not ticket:
        return None

    return ticket, list(ticket.replies)
