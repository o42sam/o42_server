from pydantic import BaseSettings

class Settings(BaseSettings):
    MONGODB_URI: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str

    class Config:
        env_file = ".env"

settings = Settings()