from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Any
from datetime import datetime, date
from enum import Enum

class Gender(str, Enum):
    male = "male"
    female = "female"
    other = "other"

class CustomerSubscriptionTier(str, Enum):
    free = "free"
    premium = "premium"
    
class BillingAddress(BaseModel):
    street: str
    city: str
    state: str
    zip_code: str

class DebitCard(BaseModel):
    cvv: str
    number: str
    expiry_date: str
    billing_address: BillingAddress
    
class CustomerBase(BaseModel):
    fName: str
    lName: str
    other_names: Optional[str] = None
    gender: Gender
    date_of_birth: date
    profile_photo: Optional[str] = None

    location: Optional[Any] = None
    email: EmailStr

class CustomerCreate(BaseModel):
    email: EmailStr
    password: str

class CustomerUpdate(BaseModel):
    fName: Optional[str] = None
    lName: Optional[str] = None
    other_names: Optional[str] = None
    gender: Optional[Gender] = None
    date_of_birth: Optional[date] = None
    profile_photo: Optional[str] = None
    location: Optional[Any] = None

class CustomerInDB(CustomerBase):
    id: str = Field(..., alias="_id")
    hashed_password: str
    isEmailVerified: bool = False
    wallet_id: Optional[str] = None
    debit_cards: List[DebitCard] = []
    subscription_tier: CustomerSubscriptionTier = CustomerSubscriptionTier.free
    created: datetime = Field(default_factory=datetime.utcnow)
    lastUpdated: datetime = Field(default_factory=datetime.utcnow)

class CustomerRegisterOut(BaseModel):
    """Response model for initial customer registration."""
    id: str
    email: EmailStr
    isEmailVerified: bool