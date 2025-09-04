from fastapi import (
    APIRouter, Depends,
    HTTPException, Request
)
from sqlalchemy.ext.asyncio import AsyncSession
from app import schemas, database, tasks
from app.websocket_manager import manager
from app.auth import get_current_user
from app.dependencies import require_user, require_agent
from app.models import User
from slowapi import Limiter
from slowapi.util import get_remote_address
from operations import ticket_operations


router = APIRouter(prefix="/tickets", tags=["Tickets"])

# Rate limiter instance
limiter = Limiter(key_func=get_remote_address)


@router.post("/", response_model=schemas.TicketRead)
@limiter.limit("5/minute")
async def create_ticket(
    payload: schemas.TicketCreate,
    request: Request,
    db: AsyncSession = Depends(database.get_db),
    current_user: User = Depends(require_user),
):
    """
    Create a new ticket for the current user.

    Args:
        payload: Ticket creation data.
        request: FastAPI request object.
        db: Database session dependency.
        current_user: The user creating the ticket.

    Returns:
        The created ticket object.
    """
    ticket = await ticket_operations.create_ticket(
        db,
        title=payload.title,
        description=payload.description,
        created_by=current_user.id
    )
    return ticket


@router.get("/{ticket_id}", response_model=schemas.TicketDetail)
async def get_ticket_detail(
    ticket_id: int,
    db: AsyncSession = Depends(database.get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get ticket details and replies. Only owner or agent can view.

    Args:
        ticket_id: ID of the ticket.
        db: Database session dependency.
        current_user: The user requesting the ticket.

    Returns:
        Ticket details and replies.

    Raises:
        HTTPException: If ticket not found or not allowed.
    """
    data = await ticket_operations.get_ticket_with_replies(db, ticket_id)
    if not data:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )
    ticket, replies = data
    # Only owner can view
    is_user = current_user.role == schemas.UserRole.user
    is_not_owner = ticket.created_by != current_user.id
    if is_user and is_not_owner:
        raise HTTPException(
            status_code=403,
            detail="Not allowed"
        )
    return schemas.TicketDetail(
        ticket=ticket,
        replies=(schemas.ReplyRead.model_validate(reply) for reply in replies)
    )


@router.post("/{ticket_id}/reply", response_model=schemas.ReplyRead)
async def add_reply(
    ticket_id: int,
    payload: schemas.ReplyCreate,
    db: AsyncSession = Depends(database.get_db),
    agent: User = Depends(require_agent),
):
    """
    Add a reply to a ticket. Only agents can reply.

    Args:
        ticket_id: ID of the ticket.
        payload: Reply creation data.
        db: Database session dependency.
        agent: The agent replying.

    Returns:
        The created reply object.

    Raises:
        HTTPException: If ticket not found.
    """
    ticket = await ticket_operations.get_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )
    reply = await ticket_operations.add_reply(
        db,
        ticket_id=ticket_id,
        message=payload.message,
        replied_by=agent.id
    )
    if not reply:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )
    # Real-time notify all WS clients in this ticket room
    await manager.broadcast(
        ticket_id, f"New reply by {agent.email}: {payload.message}"
    )
    # Celery: email ticket creator + log
    creator_email = ticket.creator.email if ticket.creator else None
    if creator_email:
        tasks.send_email_notification.delay(
            creator_email,
            f"Your ticket #{ticket_id} has a new reply."
        )
    tasks.log_reply.delay(
        ticket_id,
        payload.message,
        agent.email
    )
    return reply


@router.patch("/{ticket_id}/status", response_model=schemas.TicketRead)
async def update_status(
    ticket_id: int,
    payload: schemas.TicketStatusUpdate,
    db: AsyncSession = Depends(database.get_db),
    agent: User = Depends(require_agent),
):
    """
    Update the status of a ticket. Only agents can update status.

    Args:
        ticket_id: ID of the ticket.
        payload: Status update data.
        db: Database session dependency.
        agent: The agent updating status.

    Returns:
        The updated ticket object.

    Raises:
        HTTPException: If ticket not found.
    """
    ticket = await ticket_operations.get_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )
    ticket = await ticket_operations.change_ticket_status(
        db,
        ticket,
        payload.status
    )

    # WS broadcast
    await manager.broadcast(
        ticket_id,
        f"Status changed to {ticket.status}"
    )
    return ticket
