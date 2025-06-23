# tests/api/v1/test_messaging.py

import json
from httpx import AsyncClient
from pytest_mock import MockerFixture

# Note: httpx does not directly support WebSocket testing.
# For this, we'll use FastAPI's own TestClient which uses httpx under the hood.
from fastapi.testclient import TestClient
from app.main import app

# Use a synchronous TestClient for WebSockets as it's simpler
sync_client = TestClient(app)

async def test_send_message_rest(
    client: AsyncClient, test_customer, customer_auth_token, test_agent, mocker: MockerFixture
):
    # Mock redis publish to check if it's called
    mock_publish = mocker.patch("redis.asyncio.client.Redis.publish")
    
    headers = {"Authorization": f"Bearer {customer_auth_token}"}
    message_data = {
        "receiver_id": str(test_agent["_id"]),
        "encrypted_content": "supersecretmessage"
    }
    
    response = await client.post(
        f"{settings.API_V1_STR}/messages/send",
        headers=headers,
        json=message_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["sender_id"] == str(test_customer["_id"])
    assert data["encrypted_content"] == message_data["encrypted_content"]
    
    # Assert that we attempted to publish to Redis
    mock_publish.assert_called_once()


def test_websocket_connection(customer_auth_token: str):
    token = customer_auth_token
    with sync_client.websocket_connect(f"{settings.API_V1_STR}/ws?token={token}") as websocket:
        # If connection is made without an exception, it's successful
        # We can optionally receive an initial message if the server sends one
        # For now, just confirm connection and close
        websocket.close()