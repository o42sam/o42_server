# app/models/admin.py

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class AdminBase(BaseModel):
    email: EmailStr
    full_name: str
    is_super_admin: bool = False

class AdminCreate(AdminBase):
    password: str

class AdminUpdate(BaseModel):
    """Fields that are allowed to be updated by a super admin."""
    full_name: Optional[str] = None
    is_super_admin: Optional[bool] = None

class AdminInDB(AdminBase):
    id: str = Field(..., alias="_id")
    hashed_password: str
    created: datetime = Field(default_factory=datetime.utcnow)
    lastUpdated: datetime = Field(default_factory=datetime.utcnow)

class AdminOut(AdminBase):
    """
    Response model for sending admin data to clients.
    Excludes the hashed_password.
    """
    id: str
    created: datetime
    lastUpdated: datetime