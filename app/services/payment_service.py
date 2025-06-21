from app.core.config import settings

# Mock Paystack service
class PaystackService:
    def __init__(self, secret_key):
        self.secret_key = secret_key
        self.headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }

    async def create_virtual_account(self, email: str, fName: str, lName: str):
        """Mocks creating a Paystack Direct Virtual Account"""
        print(f"--- CREATING PAYSTACK VIRTUAL ACCOUNT for {email} ---")
        # In a real app, you would make an HTTP request to Paystack
        mock_response = {
            "status": True,
            "message": "Virtual account created",
            "data": {
                "account_name": f"{settings.PROJECT_NAME} - {fName} {lName}",
                "account_number": "9991234567",
                "bank_name": "Wema Bank",
                "paystack_account_id": f"dva_{email.split('@')[0]}"
            }
        }
        print("--- VIRTUAL ACCOUNT CREATED (MOCK) ---")
        return mock_response["data"]
        
    async def transfer_funds(self, amount_kobo: int, recipient_code: str, reason: str):
        """Mocks transferring funds to a recipient"""
        print(f"--- TRANSFERRING {amount_kobo / 100} NGN to {recipient_code} for {reason} ---")
        # In a real app, you would make an HTTP request to Paystack's transfer endpoint
        mock_response = {
            "status": True,
            "message": "Transfer successful",
        }
        print("--- TRANSFER COMPLETE (MOCK) ---")
        return mock_response

paystack_service = PaystackService(settings.PAYSTACK_SECRET_KEY)