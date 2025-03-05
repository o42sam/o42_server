import logging
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.order import Order, OrderCreate, OrderUpdate
from app.services.order_matching import match_order
from bson import ObjectId

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=Order)
async def create_order(
    order_data: OrderCreate,
    db: AsyncIOMotorClient = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    logger.info(f"Creating order type: {order_data.type}")
    order_dict = order_data.dict()
    order_dict["order_location"] = {"type": "Point", "coordinates": order_data.order_location}
    if order_data.type == "sale":
        order_dict["seller_id"] = str(current_user.id)
    else:
        order_dict["buyer_id"] = str(current_user.id)
    result = await db.o42.orders.insert_one(order_dict)
    order_id = str(result.inserted_id)
    order_dict["id"] = order_id

    # Trigger async matching
    match_order.delay(order_id)
    return Order(**order_dict)

@router.get("/{order_id}", response_model=Order)
async def read_order(order_id: str, db: AsyncIOMotorClient = Depends(get_db), current_user: dict = Depends(get_current_user)):
    logger.info(f"Fetching order: {order_id}")
    order = await db.o42.orders.find_one({"_id": ObjectId(order_id)})
    if not order or (order.get("seller_id") != str(current_user.id) and order.get("buyer_id") != str(current_user.id)):
        raise HTTPException(status_code=404, detail="Order not found or not authorized")
    order["id"] = str(order["_id"])
    return Order(**order)

@router.put("/{order_id}", response_model=Order)
async def update_order(
    order_id: str,
    order_update: OrderUpdate,
    db: AsyncIOMotorClient = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    logger.info(f"Updating order: {order_id}")
    order = await db.o42.orders.find_one({"_id": ObjectId(order_id)})
    if not order or (order.get("seller_id") != str(current_user.id) and order.get("buyer_id") != str(current_user.id)):
        raise HTTPException(status_code=403, detail="Not authorized")
    update_data = {k: v for k, v in order_update.dict(exclude_unset=True).items() if v is not None}
    if "order_location" in update_data:
        update_data["order_location"] = {"type": "Point", "coordinates": update_data["order_location"]}
    update_data["updated_at"] = datetime.utcnow()
    await db.o42.orders.update_one({"_id": ObjectId(order_id)}, {"$set": update_data})
    updated_order = await db.o42.orders.find_one({"_id": ObjectId(order_id)})
    updated_order["id"] = str(updated_order["_id"])
    return Order(**updated_order)

@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(order_id: str, db: AsyncIOMotorClient = Depends(get_db), current_user: dict = Depends(get_current_user)):
    logger.info(f"Deleting order: {order_id}")
    order = await db.o42.orders.find_one({"_id": ObjectId(order_id)})
    if not order or (order.get("seller_id") != str(current_user.id) and order.get("buyer_id") != str(current_user.id)):
        raise HTTPException(status_code=403, detail="Not authorized")
    await db.o42.orders.delete_one({"_id": ObjectId(order_id)})