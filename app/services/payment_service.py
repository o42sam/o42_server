import httpx
from typing import Dict, Any, Optional

from app.core.config import settings

PAYSTACK_BASE_URL = "https://api.paystack.co"

class PaystackService:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }

    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Helper method to make requests to Paystack API."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(method, f"{PAYSTACK_BASE_URL}{endpoint}", json=data, headers=self.headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                print(f"Paystack API Error: {e.response.status_code} - {e.response.text}")

                raise Exception(f"Paystack service failed: {e.response.json().get('message', 'Unknown error')}")
            except Exception as e:
                print(f"An unexpected error occurred with Paystack request: {e}")
                raise Exception("An unexpected error occurred with the payment service.")

    async def create_customer(self, email: str, first_name: str, last_name: str, phone: str) -> Dict[str, Any]:
        """Creates a customer on Paystack, which is required for DVA."""
        print(f"--- CREATING PAYSTACK CUSTOMER for {email} ---")
        payload = {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "phone": phone
        }
        response = await self._make_request("POST", "/customer", data=payload)
        return response.get("data")

    async def create_dedicated_virtual_account(self, customer_code: str) -> Dict[str, Any]:
        """Creates a Paystack Dedicated Virtual Account (DVA) for a customer."""
        print(f"--- CREATING PAYSTACK VIRTUAL ACCOUNT for customer {customer_code} ---")
        payload = {
            "customer": customer_code,
            "preferred_bank": "wema-bank"
        }
        response = await self._make_request("POST", "/dedicated_account", data=payload)


        return response.get("data", response)

    async def create_transfer_recipient(self, name: str, account_number: str, bank_code: str) -> Dict[str, Any]:
        """Creates a transfer recipient for withdrawals."""
        print(f"--- CREATING PAYSTACK TRANSFER RECIPIENT for {name} ({account_number}) ---")
        payload = {
            "type": "nuban",
            "name": name,
            "account_number": account_number,
            "bank_code": bank_code,
            "currency": "NGN"
        }
        response = await self._make_request("POST", "/transferrecipient", data=payload)
        return response.get("data")

    async def initiate_transfer(self, amount_kobo: int, recipient_code: str, reason: str) -> Dict[str, Any]:
        """Initiates a fund transfer to a recipient."""
        print(f"--- INITIATING TRANSFER of {amount_kobo / 100} NGN to {recipient_code} ---")
        payload = {
            "source": "balance",
            "amount": amount_kobo,
            "recipient": recipient_code,
            "reason": reason
        }
        response = await self._make_request("POST", "/transfer", data=payload)
        return response.get("data")

paystack_service = PaystackService(settings.PAYSTACK_SECRET_KEY)