from app.core.config import settings

# Mock services - in a real app, you would integrate Twilio and Brevo SDKs here.

async def send_sms(phone_number: str, message: str):
    """Mock function to send an SMS."""
    print("--- SENDING SMS ---")
    print(f"To: {phone_number}")
    print(f"Message: {message}")
    print(f"Using SID: {settings.TWILIO_ACCOUNT_SID[:5]}...")
    print("--- SMS SENT (MOCK) ---")
    return True

async def send_email(to_email: str, subject: str, body: str):
    """Mock function to send an email."""
    print("--- SENDING EMAIL ---")
    print(f"To: {to_email}")
    print(f"Subject: {subject}")
    print(f"Body: {body}")
    print(f"Using Brevo Key: {settings.BREVO_API_KEY[:5]}...")
    print("--- EMAIL SENT (MOCK) ---")
    return True