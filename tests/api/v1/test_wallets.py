# tests/api/v1/test_wallets.py

from httpx import AsyncClient
import pyotp

from app.core.config import settings

async def test_get_my_wallet(client: AsyncClient, agent_auth_token: str):
    headers = {"Authorization": f"Bearer {agent_auth_token}"}
    response = await client.get(f"{settings.API_V1_STR}/wallets/me", headers=headers)
    
    assert response.status_code == 200
    wallet_data = response.json()
    assert wallet_data["balance"] == 50000.00

async def test_withdraw_success(client: AsyncClient, test_agent: dict, agent_auth_token: str):
    headers = {"Authorization": f"Bearer {agent_auth_token}"}
    # Generate a valid 2FA code from the agent's secret
    valid_code = pyotp.TOTP(test_agent["two_fa_secret"]).now()
    
    payload = {
        "amount": 10000.00,
        "two_fa_code": valid_code
    }
    
    response = await client.post(f"{settings.API_V1_STR}/wallets/withdraw", headers=headers, json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Withdrawal request received and is being processed."
    assert data["new_balance"] == 40000.00

async def test_withdraw_insufficient_funds(client: AsyncClient, test_agent: dict, agent_auth_token: str):
    headers = {"Authorization": f"Bearer {agent_auth_token}"}
    valid_code = pyotp.TOTP(test_agent["two_fa_secret"]).now()

    payload = {
        "amount": 90000.00, # More than the 50000 balance
        "two_fa_code": valid_code
    }
    
    response = await client.post(f"{settings.API_V1_STR}/wallets/withdraw", headers=headers, json=payload)
    
    assert response.status_code == 400
    assert response.json()["detail"] == "Insufficient wallet balance."
    
async def test_withdraw_invalid_2fa(client: AsyncClient, agent_auth_token: str):
    headers = {"Authorization": f"Bearer {agent_auth_token}"}
    payload = {
        "amount": 10000.00,
        "two_fa_code": "000000" # Invalid code
    }
    
    response = await client.post(f"{settings.API_V1_STR}/wallets/withdraw", headers=headers, json=payload)
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid 2FA code."