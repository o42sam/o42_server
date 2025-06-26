from app.crud import CRUDBase
from app.models.message import MessageCreate, MessageUpdate

class CRUDMessage(CRUDBase[MessageCreate, MessageUpdate]):
    pass

message = CRUDMessage("messages")