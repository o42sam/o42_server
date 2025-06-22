from fastapi import HTTPException
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import brevo
from brevo.rest import ApiException

from app.core.config import settings

# --- Twilio SMS Service ---
try:
    twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
except Exception as e:
    print(f"Warning: Could not initialize Twilio client. {e}")
    twilio_client = None

async def send_sms(phone_number: str, message: str):
    """
    Sends an SMS using the Twilio API.
    """
    if not twilio_client:
        print("--- TWILIO CLIENT NOT INITIALIZED (SKIPPING SMS) ---")
        return False
        
    print(f"--- SENDING SMS TO {phone_number} ---")
    try:
        message_instance = twilio_client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        print(f"--- SMS SENT SUCCESSFULLY (SID: {message_instance.sid}) ---")
        return True
    except TwilioRestException as e:
        print(f"Error: Failed to send SMS via Twilio. {e}")
        # In a real app, you might want to handle different error codes differently
        raise HTTPException(status_code=500, detail=f"Failed to send SMS: {e.msg}")
    except Exception as e:
        print(f"An unexpected error occurred with Twilio: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while sending SMS.")


# --- Brevo Email Service ---
brevo_config = brevo.Configuration()
brevo_config.api_key['api-key'] = settings.BREVO_API_KEY
brevo_api_instance = brevo.TransactionalEmailsApi(brevo.ApiClient(brevo_config))

async def send_email(to_email: str, subject: str, html_content: str):
    """
    Sends an email using the Brevo API.
    """
    print(f"--- SENDING EMAIL TO {to_email} ---")
    sender = brevo.SendSmtpEmailSender(
        name=settings.PROJECT_NAME, 
        email=f"noreply@{settings.PROJECT_NAME.lower().replace(' ', '')}.com"
    )
    to = [brevo.SendSmtpEmailTo(email=to_email)]
    
    smtp_email = brevo.SendSmtpEmail(
        to=to,
        sender=sender,
        subject=subject,
        html_content=html_content
    )

    try:
        api_response = brevo_api_instance.send_transac_email(smtp_email)
        print(f"--- EMAIL SENT SUCCESSFULLY (Message ID: {api_response.message_id}) ---")
        return True
    except ApiException as e:
        print(f"Error: Failed to send email via Brevo. {e.body}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {e.reason}")
    except Exception as e:
        print(f"An unexpected error occurred with Brevo: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while sending email.")