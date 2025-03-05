from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional

class PersonalIdentification(BaseModel):
    id_name: str
    id_photo: str
    id_number: str

class AgentBase(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: datetime
    email: EmailStr
    personal_identification: PersonalIdentification
    phone_number: str
    location: List[float]  # [lon, lat]
    mobility: bool

class AgentCreate(AgentBase):
    password: str

class AgentUpdate(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    date_of_birth: Optional[datetime]
    email: Optional[EmailStr]
    phone_number: Optional[str]
    location: Optional[List[float]]
    mobility: Optional[bool]

class Agent(AgentBase):
    id: str
    password: str
    face_encoding: Optional[List[float]]
    email_verified: bool = False
    phone_verified: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        arbitrary_types_allowed = True