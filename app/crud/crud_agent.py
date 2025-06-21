from typing import Optional, Dict
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.crud import CRUDBase
from app.models.agent import AgentCreate, AgentUpdate

class CRUDAgent(CRUDBase[AgentCreate, AgentUpdate]):
    async def get_by_email(self, db: AsyncIOMotorDatabase, *, email: str) -> Optional[Dict]:
        return await db[self.collection_name].find_one({"email": email})

agent = CRUDAgent("agents")