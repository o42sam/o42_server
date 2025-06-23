from app.core.config import settings
from httpx import AsyncClient

async def test_register_customer(client: AsyncClient):
    response = await client.post(
        f"{settings.API_V1_STR}/customers/register",
        json={"email": "newcustomer@example.com", "password": "newpassword"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newcustomer@example.com"
    assert "hashed_password" in data

async def test_get_customer_me(client: AsyncClient, customer_auth_token: str):
    headers = {"Authorization": f"Bearer {customer_auth_token}"}
    response = await client.get(f"{settings.API_V1_STR}/customers/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testcustomer@example.com"

async def test_get_customer_me_unauthenticated(client: AsyncClient):
    response = await client.get(f"{settings.API_V1_STR}/customers/me")
    assert response.status_code == 401 # or 403 depending on your setup