from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from routers import auth_router, ticket_router, websocket_router


limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Support Ticket System")

# SlowAPI setup
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Include routers
app.include_router(auth_router.router)
app.include_router(ticket_router.router)
app.include_router(websocket_router.router)
