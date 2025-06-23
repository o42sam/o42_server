from app.core.config import settings
from httpx import AsyncClient

async def test_login_success(client: AsyncClient, test_customer: dict):
    response = await client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": test_customer["email"], "password": "testpassword"},
    )
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

async def test_login_wrong_password(client: AsyncClient, test_customer: dict):
    response = await client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": test_customer["email"], "password": "wrongpassword"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Incorrect email or password"