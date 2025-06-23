import asyncio
import pytest
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import AsyncGenerator, Generator

from app.main import app
from app.core.config import settings
from app.core import security
from app.db.mongodb import get_db
from app.models.wallet import WalletCreate

# --- Database Fixtures ---

@pytest.fixture(scope="function")
async def test_agent(db: AsyncIOMotorDatabase) -> dict:
    """
    Creates a test agent directly in the database, now including a wallet and 2FA.
    """
    # Create the agent
    agent_data = {
        "email": "testagent@example.com",
        "hashed_password": security.get_password_hash("testpassword"),
        "fName": "Test",
        "lName": "Agent",
        "isEmailVerified": True,
        "phone_number": "+1234567890",
        "isPhoneNumberVerified": True,
        "user_type": "agent",
        "two_fa_secret": security.generate_2fa_secret(), # Add a 2FA secret
        "location": {"type": "Point", "coordinates": [3.3792, 6.5244]}
    }
    result = await db.agents.insert_one(agent_data)
    created_agent = await db.agents.find_one({"_id": result.inserted_id})

    # Create a wallet for the agent
    wallet_in = WalletCreate(owner_id=str(created_agent["_id"]), balance=50000.00)
    await db.wallets.insert_one(wallet_in.model_dump())
    
    return created_agent

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_db_client() -> AsyncIOMotorClient:
    """Create a Motor client for the test database."""
    # Use a separate database for testing
    test_mongo_details = f"{settings.MONGO_DETAILS}_test"
    client = AsyncIOMotorClient(test_mongo_details)
    yield client
    client.close()

@pytest.fixture(scope="function")
async def db(test_db_client: AsyncIOMotorClient) -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """
    Provides a clean test database for each test function.
    Clears all collections after the test runs.
    """
    test_db_name = f"{settings.DB_NAME}_test"
    db = test_db_client[test_db_name]
    
    # Yield the database session to the test
    yield db
    
    # Teardown: drop all collections in the test database
    collections = await db.list_collection_names()
    for collection_name in collections:
        await db.drop_collection(collection_name)


# --- Application Client Fixture ---

@pytest.fixture(scope="function")
async def client(db: AsyncIOMotorDatabase) -> AsyncGenerator[AsyncClient, None]:
    """
    Create a new FastAPI TestClient that uses the `db` fixture to override
    the `get_db` dependency that is injected into routes.
    """
    async def get_test_db():
        yield db

    app.dependency_overrides[get_db] = get_test_db
    
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c
    
    # Clean up dependency overrides
    app.dependency_overrides.clear()


# --- Mock User and Auth Fixtures ---

@pytest.fixture(scope="function")
async def test_customer(db: AsyncIOMotorDatabase) -> dict:
    """Creates a test customer directly in the database."""
    customer_data = {
        "email": "testcustomer@example.com",
        "hashed_password": security.get_password_hash("testpassword"),
        "fName": "Test",
        "lName": "Customer",
        "isEmailVerified": True,
        "user_type": "customer"
    }
    result = await db.customers.insert_one(customer_data)
    created_customer = await db.customers.find_one({"_id": result.inserted_id})
    return created_customer


@pytest.fixture(scope="function")
async def test_agent(db: AsyncIOMotorDatabase) -> dict:
    """Creates a test agent directly in the database."""
    agent_data = {
        "email": "testagent@example.com",
        "hashed_password": security.get_password_hash("testpassword"),
        "fName": "Test",
        "lName": "Agent",
        "isEmailVerified": True,
        "phone_number": "+1234567890",
        "isPhoneNumberVerified": True,
        "user_type": "agent",
        "location": {"type": "Point", "coordinates": [3.3792, 6.5244]} # Lagos coordinates
    }
    result = await db.agents.insert_one(agent_data)
    created_agent = await db.agents.find_one({"_id": result.inserted_id})
    return created_agent


@pytest.fixture(scope="function")
def customer_auth_token(test_customer: dict) -> str:
    """Returns a valid JWT for the test customer."""
    return security.create_access_token(subject=str(test_customer["_id"]))


@pytest.fixture(scope="function")
def agent_auth_token(test_agent: dict) -> str:
    """Returns a valid JWT for the test agent."""
    return security.create_access_token(subject=str(test_agent["_id"]))