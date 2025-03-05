import logging
from twilio.rest import Client
from app.core.config import settings

logger = logging.getLogger(__name__)

def send_verification_sms(to_phone: str, code: str):
    logger.info(f"Sending verification SMS to: {to_phone}")
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    message = client.messages.create(
        body=f"Your o42 verification code is: {code}",
        from_=settings.TWILIO_PHONE_NUMBER,
        to=to_phone
    )
    return message.sid