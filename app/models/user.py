from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any
from datetime import datetime, date
from .customer import Gender # Reuse Gender enum

class UserMeResponse(BaseModel):
    # Core fields required for everyone
    id: str
    email: EmailStr
    user_type: str # 'customer', 'agent', or 'admin'

    # Optional fields that may not be set yet
    fName: Optional[str] = None
    lName: Optional[str] = None
    gender: Optional[Gender] = None
    date_of_birth: Optional[date] = None
    profile_photo: Optional[str] = None
    location: Optional[Any] = None
    wallet_id: Optional[str] = None
    isEmailVerified: bool = False
    
    # Agent-specific optional fields
    phone_number: Optional[str] = None
    isPhoneNumberVerified: bool = False