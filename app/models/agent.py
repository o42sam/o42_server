from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Any
from datetime import datetime, date
from enum import Enum
from app.models.customer import Gender

class AgentSubscriptionTier(str, Enum):
    starter = "starter"
    runner = "runner"
    tycoon = "tycoon"

class AgentBase(BaseModel):
    fName: str
    lName: str
    other_names: Optional[str] = None
    gender: Gender
    date_of_birth: date
    profile_photo: Optional[str] = None

    location: Optional[Any] = None
    email: EmailStr
    phone_number: Optional[str] = None

class AgentCreate(BaseModel):
    email: EmailStr
    password: str
    phone_number: str

class AgentUpdate(BaseModel):
    fName: Optional[str] = None
    lName: Optional[str] = None
    other_names: Optional[str] = None
    gender: Optional[Gender] = None
    date_of_birth: Optional[date] = None
    profile_photo: Optional[str] = None
    location: Optional[Any] = None
    phone_number: Optional[str] = None

class AgentInDB(AgentBase):
    id: str = Field(..., alias="_id")
    hashed_password: str
    isEmailVerified: bool = False
    isPhoneNumberVerified: bool = False
    personal_identification: Optional[str] = None
    isPersonalIdentificationVerified: bool = False
    face_mapping: Optional[Any] = None
    subscription_tier: AgentSubscriptionTier = AgentSubscriptionTier.starter
    wallet_id: Optional[str] = None
    two_fa_secret: Optional[str] = None
    created: datetime = Field(default_factory=datetime.utcnow)
    lastUpdated: datetime = Field(default_factory=datetime.utcnow)

class AgentRegisterOut(BaseModel):
    """Response model for initial agent registration."""
    id: str
    email: EmailStr
    phone_number: str
    isEmailVerified: bool
    isPhoneNumberVerified: bool