import contextlib
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app import schemas, auth
from app.main import app
from operations import ticket_operations, auth_operation
from app.schemas import UserRole
from app.websocket_manager import manager
from app.dependencies import require_user, require_agent


@pytest.fixture
def override_dependencies():
    """
    Fixture to simplify dependency overrides.
    Accepts a dict of dependency -> return_value.
    Clears overrides after each test.
    """
    @contextlib.contextmanager
    def apply(overrides: dict):
        try:
            for dep, value in overrides.items():
                app.dependency_overrides[dep] = lambda value=value: value
            yield
        finally:
            app.dependency_overrides.clear()
    return apply


async def create_test_user(
        db_session: AsyncSession,
        email: str,
        password: str,
        role: UserRole):
    """
    Function to create a test user in the database.
    """
    hashed_password = auth.hash_password(password)
    user = await auth_operation.create_user(
        db=db_session,
        email=email,
        hashed_password=hashed_password,
        role=role
    )
    return user


@pytest.mark.asyncio
async def test_create_ticket(db_session: AsyncSession):
    """
    Testcase for ticket creation.
    """
    user = await create_test_user(
        db_session,
        "user1@example.com",
        "password",
        UserRole.user
        )
    ticket = await ticket_operations.create_ticket(
        db=db_session,
        title="Test Ticket",
        description="This is a test",
        created_by=user.id
    )
    assert ticket.id is not None
    assert ticket.title == "Test Ticket"
    assert ticket.description == "This is a test"
    assert ticket.created_by == user.id


@pytest.mark.asyncio
async def test_get_ticket_and_replies(db_session: AsyncSession):
    """
    Testcase retrieving a ticket along with its replies.
    """
    user = await create_test_user(
        db_session,
        "user2@example.com",
        "password",
        UserRole.user)
    ticket = await ticket_operations.create_ticket(
        db_session,
        "Ticket 2",
        "Desc",
        user.id
        )

    # Add a reply to the ticket
    reply = await ticket_operations.add_reply(
        db_session,
        ticket.id,
        "First reply",
        user.id
        )

    # Fetch ticket with replies and validate
    result = await ticket_operations.get_ticket_with_replies(
        db_session,
        ticket.id
        )
    assert result is not None
    ticket, replies = result
    assert ticket.id == ticket.id
    assert len(replies) == 1
    assert replies[0].message == "First reply"


@pytest.mark.asyncio
async def test_change_ticket_status(db_session: AsyncSession):
    """
    Testcase changing the status of a ticket.
    """
    user = await create_test_user(
        db_session,
        "user3@example.com",
        "password",
        UserRole.agent
        )
    ticket = await ticket_operations.create_ticket(
        db_session,
        "Ticket Status",
        None,
        user.id
        )

    # Update status to 'close'
    updated_ticket = await ticket_operations.change_ticket_status(
        db_session, ticket, schemas.TicketStatus.close
    )
    assert updated_ticket.status == schemas.TicketStatus.close


@pytest.mark.asyncio
async def test_create_ticket_api(
        client: AsyncClient,
        db_session: AsyncSession,
        override_dependencies
        ):
    """
    Testcase for testing the API endpoint for creating a new ticket.
    """
    user = await create_test_user(
        db_session,
        "api_user@example.com",
        "password",
        UserRole.user
        )

    with override_dependencies({
        auth.get_current_user: user,
        require_user: user
    }):
        payload = {"title": "API Ticket", "description": "Ticket via API"}
        response = await client.post("/tickets/", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == payload["title"]
        assert data["description"] == payload["description"]


@pytest.mark.asyncio
async def test_update_ticket_status_api(
        client: AsyncClient,
        db_session: AsyncSession,
        override_dependencies
        ):
    """
    Testcase for testing the API endpoint for updating a ticket's status.
    """
    user = await create_test_user(
        db_session,
        "user5@example.com",
        "password",
        UserRole.user
        )
    agent = await create_test_user(
        db_session,
        "agent2@example.com",
        "password",
        UserRole.agent
        )
    ticket = await ticket_operations.create_ticket(
        db_session,
        "Status API",
        None,
        user.id
        )

    with override_dependencies({
        auth.get_current_user: agent,
        require_agent: agent
    }):
        payload = {"status": "close"}
        response = await client.patch(f"/tickets/{ticket.id}/status", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "close"


@pytest.mark.asyncio
async def test_get_ticket_detail_api(
        client: AsyncClient,
        db_session: AsyncSession,
        override_dependencies
        ):
    """
    Test the API endpoint for retrieving detailed ticket information.
    """
    user = await create_test_user(
        db_session,
        "user6@example.com",
        "password",
        UserRole.user
        )
    ticket = await ticket_operations.create_ticket(
        db_session,
        "Detail API",
        "Detail desc",
        user.id
        )

    with override_dependencies({
        auth.get_current_user: user,
        require_user: user
    }):
        response = await client.get(f"/tickets/{ticket.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["ticket"]["id"] == ticket.id


@pytest.mark.asyncio
async def test_websocket_connect_and_broadcast(db_session: AsyncSession):
    """
    Testcase for WebSocket connection and broadcast functionality.
    """
    # Create a ticket and test agent
    user = await create_test_user(
        db_session,
        "ws_user@example.com",
        "password",
        UserRole.user
        )
    agent = await create_test_user(
        db_session,
        "ws_agent@example.com",
        "password",
        UserRole.agent
        )
    ticket = await ticket_operations.create_ticket(
        db_session,
        "WS Ticket",
        None,
        user.id
        )

    class DummyWebSocket:
        """
        Dummy WebSocket implementation for testing.
        Stores sent messages and tracks connection state.
        """
        def __init__(self):
            self.accepted = False
            self.sent_messages = []

        async def accept(self):
            self.accepted = True  # Simulate successful connection

        async def send_text(self, message: str):
            self.sent_messages.append(message)  # Capture broadcasted messages

    ws = DummyWebSocket()

    # Connect dummy WebSocket client
    await manager.connect(ticket.id, ws)
    assert ws in manager.active[ticket.id]
    assert ws.accepted is True

    # Broadcast message and verify delivery
    message = "New reply from agent"
    await manager.broadcast(ticket.id, message)
    assert message in ws.sent_messages

    # Disconnect and ensure cleanup
    manager.disconnect(ticket.id, ws)
    assert ws not in manager.active[ticket.id]
