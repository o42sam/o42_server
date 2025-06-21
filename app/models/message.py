from pydantic import BaseModel, Field
from datetime import datetime

class MessageBase(BaseModel):
    sender_id: str
    receiver_id: str
    encrypted_content: str

class MessageCreate(MessageBase):
    pass

class MessageInDB(MessageBase):
    id: str = Field(..., alias="_id")
    created: datetime = Field(default_factory=datetime.utcnow)