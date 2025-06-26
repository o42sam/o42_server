from typing import List, Dict
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.crud import CRUDBase
from app.models.order import SaleOrderCreate, PurchaseOrderCreate, SaleOrderUpdate, PurchaseOrderUpdate


class CRUDSaleOrder(CRUDBase[SaleOrderCreate, SaleOrderUpdate]):
    async def get_by_creator(self, db: AsyncIOMotorDatabase, *, creator_id: str) -> List[Dict]:
        cursor = db[self.collection_name].find({"creator_id": creator_id})
        return await cursor.to_list(length=None)

class CRUDPurchaseOrder(CRUDBase[PurchaseOrderCreate, PurchaseOrderUpdate]):
    async def get_by_creator(self, db: AsyncIOMotorDatabase, *, creator_id: str) -> List[Dict]:
        cursor = db[self.collection_name].find({"creator_id": creator_id})
        return await cursor.to_list(length=None)

sale_order = CRUDSaleOrder("sale_orders")
purchase_order = CRUDPurchaseOrder("purchase_orders")