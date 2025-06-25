from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1 import agents, auth, customers, messaging, orders, wallets, admin, analytics
from app.core.config import settings
from app.db.mongodb import close_mongo_connection, connect_to_mongo
from app.db.redis_client import close_redis_connection, connect_to_redis
from app.utils.limiter import limiter


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)


app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


app.add_event_handler("startup", connect_to_mongo)
app.add_event_handler("startup", connect_to_redis)
app.add_event_handler("shutdown", close_mongo_connection)
app.add_event_handler("shutdown", close_redis_connection)


# if settings.CLIENT_ORIGIN:
#     app.add_middleware(
#         CORSMiddleware,
#         allow_origins=[settings.CLIENT_ORIGIN],
#         allow_credentials=True,
#         allow_methods=["*"],
#         allow_headers=["*"],
#     )
origins = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods
    allow_headers=["*"], # Allows all headers
)

app.include_router(auth.router, prefix=settings.API_V1_STR, tags=["Authentication"])
app.include_router(customers.router, prefix=settings.API_V1_STR, tags=["Customers"])
app.include_router(agents.router, prefix=settings.API_V1_STR, tags=["Agents"])
app.include_router(orders.router, prefix=settings.API_V1_STR, tags=["Orders"])
app.include_router(wallets.router, prefix=settings.API_V1_STR, tags=["Wallets & Payments"])
app.include_router(messaging.router, prefix=settings.API_V1_STR, tags=["Messaging"])
app.include_router(admin.router, prefix=settings.API_V1_STR, tags=["Admin"])
app.include_router(analytics.router, prefix=settings.API_V1_STR, tags=["Analytics"])

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}