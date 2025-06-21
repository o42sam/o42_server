from typing import Optional, Dict
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.crud import CRUDBase
from app.models.customer import CustomerCreate, CustomerUpdate


class CRUDCustomer(CRUDBase[CustomerCreate, CustomerUpdate]):
    async def get_by_email(self, db: AsyncIOMotorDatabase, *, email: str) -> Optional[Dict]:
        return await db[self.collection_name].find_one({"email": email})

customer = CRUDCustomer("customers")