from app.crud import CRUDBase
from app.models.notification import NotificationCreate
from pydantic import BaseModel

class NotificationUpdate(BaseModel):
    pass

class CRUDNotification(CRUDBase[NotificationCreate, NotificationUpdate]):
    pass

notification = CRUDNotification("notifications")