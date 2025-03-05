import logging
import aiosmtplib
from email.mime.text import MIMEText
from app.core.config import settings

logger = logging.getLogger(__name__)

async def send_verification_email(to_email: str, code: str):
    logger.info(f"Sending verification email to: {to_email}")
    msg = MIMEText(f"Your verification code is: {code}")
    msg["Subject"] = "o42 Email Verification"
    msg["From"] = settings.SMTP_USER
    msg["To"] = to_email
    await aiosmtplib.send(
        msg,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
        use_tls=True
    )