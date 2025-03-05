from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class CustomerBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr

class CustomerCreate(CustomerBase):
    password: str

class CustomerUpdate(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[EmailStr]

class Customer(CustomerBase):
    id: str
    password: str
    email_verified: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        arbitrary_types_allowed = True