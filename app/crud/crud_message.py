from app.crud import CRUDBase
from app.models.message import MessageCreate
from pydantic import BaseModel

# A placeholder for update schema if needed in the future
class MessageUpdate(BaseModel):
    pass

class CRUDMessage(CRUDBase[MessageCreate, MessageUpdate]):
    pass

message = CRUDMessage("messages")