from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket_manager import manager


router = APIRouter()


@router.websocket("/ws/tickets/{ticket_id}")
async def ticket_ws(ticket_id: int, websocket: WebSocket):
    """
    WebSocket endpoint for ticket room communication.
    Authenticates using token query param.
    """
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4401)
        return

    try:
        await manager.connect(ticket_id, websocket)
        while True:
            incoming_messages = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ticket_id, websocket)
