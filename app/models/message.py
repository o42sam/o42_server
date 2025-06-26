from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class MessageBase(BaseModel):
    sender_id: str
    receiver_id: str
    encrypted_content: str

class MessageCreate(MessageBase):
    pass

class MessageInDB(MessageBase):
    id: str = Field(..., alias="_id")
    created: datetime = Field(default_factory=datetime.utcnow)

class MessageUpdate(BaseModel):
    """Defines fields that can be updated for a Message."""
    encrypted_content: Optional[str] = None