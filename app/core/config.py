from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "o42 Marketplace"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    CLIENT_ORIGIN: str


    MONGO_DETAILS: str
    DB_NAME: str
    REDIS_HOST: str
    REDIS_PORT: int


    AGENT_LINKING_RADIUS_KM: int = 10
    MIN_WALLET_BALANCE_FOR_PURCHASE: int = 1000
    DEFAULT_SALE_COMMISSION: float = 0.10
    TRANSACTION_FEE_PERCENTAGE: float = 0.005
    STARTER_AGENT_WITHDRAWAL_DAYS: int = 7


    AGENT_TYCOON_PRICE: int
    AGENT_RUNNER_PRICE: int
    CUSTOMER_PREMIUM_PRICE: int


    PAYSTACK_SECRET_KEY: str
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str
    BREVO_API_KEY: str
    GOOGLE_API_KEY: str
    GOOGLE_CSE_ID: str
    GOOGLE_CLOUD_PROJECT: str
    GOOGLE_CLOUD_REGION: str
    GCS_BUCKET_NAME: str

    SYSTEM_ADMIN_USER_ID: str = "042_MARKETPLACE_ADMIN"

    class Config:
        env_file = ".env"

settings = Settings()