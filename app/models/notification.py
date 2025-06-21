from pydantic import BaseModel, Field
from datetime import datetime

class NotificationBase(BaseModel):
    target_user_id: str
    subject: str
    message: str

class NotificationCreate(NotificationBase):
    pass

class NotificationInDB(NotificationBase):
    id: str = Field(..., alias="_id")
    is_read: bool = False
    created: datetime = Field(default_factory=datetime.utcnow)
    lastUpdated: datetime = Field(default_factory=datetime.utcnow)