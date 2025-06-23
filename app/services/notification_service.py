

from fastapi import HTTPException
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi.encoders import jsonable_encoder

from app.core.config import settings
from app.crud import crud_notification, crud_message
from app.models.notification import NotificationCreate
from app.models.message import MessageCreate



try:
    twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
except Exception as e:
    print(f"Warning: Could not initialize Twilio client. {e}")
    twilio_client = None

async def send_sms(phone_number: str, message: str):

    if not twilio_client:
        print("--- TWILIO CLIENT NOT INITIALIZED (SKIPPING SMS) ---")
        return False
    print(f"--- SENDING SMS TO {phone_number} ---")
    try:
        message_instance = twilio_client.messages.create(body=message, from_=settings.TWILIO_PHONE_NUMBER, to=phone_number)
        print(f"--- SMS SENT SUCCESSFULLY (SID: {message_instance.sid}) ---")
        return True
    except TwilioRestException as e:
        print(f"Error: Failed to send SMS via Twilio. {e}")

        return False



brevo_config = sib_api_v3_sdk.Configuration()
brevo_config.api_key['api-key'] = settings.BREVO_API_KEY
brevo_api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(brevo_config))

async def send_email(to_email: str, subject: str, html_content: str):

    print(f"--- SENDING EMAIL TO {to_email} ---")
    sender = sib_api_v3_sdk.SendSmtpEmailSender(name=settings.PROJECT_NAME, email=f"noreply@{settings.PROJECT_NAME.lower().replace(' ', '')}.com")
    to = [sib_api_v3_sdk.SendSmtpEmailTo(email=to_email)]
    smtp_email = sib_api_v3_sdk.SendSmtpEmail(to=to, sender=sender, subject=subject, html_content=html_content)
    try:
        api_response = brevo_api_instance.send_transac_email(smtp_email)
        print(f"--- EMAIL SENT SUCCESSFULLY (Message ID: {api_response.message_id}) ---")
        return True
    except ApiException as e:
        print(f"Error: Failed to send email via Brevo. {e.body}")
        return False



async def create_and_dispatch_notification(
    db: AsyncIOMotorDatabase,
    target_user: dict,
    subject: str,
    message_body: str
):
    """
    Creates, stores, and sends a notification through all channels,
    including as an in-app message.
    """
    target_user_id = str(target_user["_id"])
    

    notif_in = NotificationCreate(target_user_id=target_user_id, subject=subject, message=message_body)
    await crud_notification.notification.create(db, obj_in=notif_in)
    

    if target_user.get("email"):
        await send_email(to_email=target_user["email"], subject=subject, html_content=f"<p>{message_body}</p>")
    if target_user.get("phone_number"):
        await send_sms(phone_number=target_user["phone_number"], message=message_body)
        

    message_in = MessageCreate(
        sender_id=settings.SYSTEM_ADMIN_USER_ID,
        receiver_id=target_user_id,


        encrypted_content=message_body
    )
    created_message = await crud_message.message.create(db, obj_in=message_in)
    message_data = jsonable_encoder(created_message)


    await manager.send_personal_message(message_data, target_user_id)
    
    print(f"Dispatched notification and in-app message to user {target_user_id}")