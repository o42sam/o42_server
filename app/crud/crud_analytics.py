from app.crud import CRUDBase
from app.models.analytics import DailyAnalyticsSnapshot
from pydantic import BaseModel

class AnalyticsUpdate(BaseModel): # Placeholder
    pass

class CRUDAnalytics(CRUDBase[DailyAnalyticsSnapshot, AnalyticsUpdate]):
    pass

analytics = CRUDAnalytics("analytics")