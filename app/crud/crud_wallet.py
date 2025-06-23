from typing import Optional, Dict
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.crud import CRUDBase
from app.models.wallet import WalletCreate, Transaction
from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder
class UpdateSchema(BaseModel):
    pass

class CRUDWallet(CRUDBase[WalletCreate, UpdateSchema]):
    async def get_by_owner_id(self, db: AsyncIOMotorDatabase, *, owner_id: str) -> Optional[Dict]:
        return await db[self.collection_name].find_one({"owner_id": owner_id})

    # MODIFIED: Override the base create method to include the paystack_id
    async def create(self, db: AsyncIOMotorDatabase, *, obj_in: WalletCreate, paystack_id: str) -> Dict:
        obj_in_data = jsonable_encoder(obj_in)
        # Add the paystack_account_id to the data before inserting
        obj_in_data["paystack_account_id"] = paystack_id
        
        result = await db[self.collection_name].insert_one(obj_in_data)
        created_record = await self.get(db, result.inserted_id)
        return created_record

class CRUDTransaction:
    # ... (this class remains unchanged)
    async def create(self, db: AsyncIOMotorDatabase, *, transaction_in: Transaction) -> Dict:
        trans_data = transaction_in.model_dump(by_alias=True, exclude=["id"])
        result = await db["transactions"].insert_one(trans_data)
        created = await db["transactions"].find_one({"_id": result.inserted_id})
        return created

wallet = CRUDWallet("wallets")
transaction = CRUDTransaction()