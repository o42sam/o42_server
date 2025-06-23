from typing import Optional, Dict
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.crud import CRUDBase
from app.models.admin import AdminCreate
from pydantic import BaseModel

class AdminUpdate(BaseModel):
    pass

class CRUDAdmin(CRUDBase[AdminCreate, AdminUpdate]):
    async def get_by_email(self, db: AsyncIOMotorDatabase, *, email: str) -> Optional[Dict]:
        return await db[self.collection_name].find_one({"email": email})

admin = CRUDAdmin("admins")