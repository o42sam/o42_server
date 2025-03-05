import logging
from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.endpoints import agents, customers, auth, orders, utils

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("o42.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="o42 Backend", version="0.1.0", docs_url="/docs")

# Include API versioned routers
app.include_router(agents.router, prefix="/v1/agents", tags=["agents"])
app.include_router(customers.router, prefix="/v1/customers", tags=["customers"])
app.include_router(auth.router, prefix="/v1/auth", tags=["auth"])
app.include_router(orders.router, prefix="/v1/orders", tags=["orders"])
app.include_router(utils.router, prefix="/v1/utils", tags=["utils"])

@app.on_event("startup")
async def startup_event():
    logger.info("Starting o42 Backend...")