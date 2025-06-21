from typing import Optional, Dict
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.crud import CRUDBase
from app.models.wallet import WalletCreate, Transaction
from pydantic import BaseModel

class UpdateSchema(BaseModel):
    pass

class CRUDWallet(CRUDBase[WalletCreate, UpdateSchema]):
    async def get_by_owner_id(self, db: AsyncIOMotorDatabase, *, owner_id: str) -> Optional[Dict]:
        return await db[self.collection_name].find_one({"owner_id": owner_id})

class CRUDTransaction:
    async def create(self, db: AsyncIOMotorDatabase, *, transaction_in: Transaction) -> Dict:
        trans_data = transaction_in.model_dump(by_alias=True, exclude=["id"])
        result = await db["transactions"].insert_one(trans_data)
        created = await db["transactions"].find_one({"_id": result.inserted_id})
        return created

wallet = CRUDWallet("wallets")
transaction = CRUDTransaction()