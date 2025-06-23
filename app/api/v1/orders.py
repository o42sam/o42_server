# app/api/v1/orders.py

from fastapi import APIRouter, Depends, Body, HTTPException, BackgroundTasks, status
from typing import Dict, Any

from app.crud import purchase_order, sale_order # <-- CORRECTED IMPORT
from app.db.mongodb import get_db
from app.models.order import (
    PurchaseOrderCreate, PurchaseOrderCreateIn, PurchaseOrderInDB,
    SaleOrderCreate, SaleOrderInDB
)
from app.api.deps import get_current_active_customer, get_current_user
from app.services import image_generation, geo
from app.services.notification_service import create_and_dispatch_notification
from app.services.matching_service import run_matching_cycle

router = APIRouter()

# --- Purchase Order Endpoints ---

@router.post("/orders/purchase", response_model=PurchaseOrderInDB, status_code=status.HTTP_201_CREATED)
async def create_purchase_order(
    order_in: PurchaseOrderCreateIn,
    background_tasks: BackgroundTasks,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_active_customer),
):
    order_data = order_in.model_dump()
    order_data["creator_id"] = str(current_user["_id"])
    order_to_create = PurchaseOrderCreate(**order_data)
    new_order = await purchase_order.create(db, obj_in=order_to_create)
    
    longitude = current_user.get("location", {}).get("coordinates", [0, 0])[0]
    latitude = current_user.get("location", {}).get("coordinates", [0, 0])[1]
    nearby_agents = await geo.get_agents_in_radius(db, longitude, latitude)
    
    await purchase_order.update(db, db_obj=new_order, obj_in={"linked_agents_ids": [str(a["_id"]) for a in nearby_agents]})
    
    for agent in nearby_agents:
        subject = "New Order Alert!"
        message_body = f"You have been linked to a new purchase order created near you. Order ID: {str(new_order['_id'])}"
        await create_and_dispatch_notification(db, target_user=agent, subject=subject, message_body=message_body)

    background_tasks.add_task(run_matching_cycle, db, str(new_order["_id"]), "purchase")

    return new_order

@router.put("/orders/purchase/{order_id}", response_model=PurchaseOrderInDB)
async def update_purchase_order(
    order_id: str,
    update_data: Dict[str, Any],
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    order = await purchase_order.get(db, id=order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase order not found")
    if order["creator_id"] != str(current_user["_id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this order")
        
    updated_order = await purchase_order.update(db, db_obj=order, obj_in=update_data)
    return updated_order

@router.delete("/orders/purchase/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_purchase_order(
    order_id: str,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    order = await purchase_order.get(db, id=order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase order not found")
    if order["creator_id"] != str(current_user["_id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this order")
    
    await purchase_order.remove(db, id=order_id)
    return

# --- Sale Order Endpoints ---

@router.post("/orders/sale", response_model=SaleOrderInDB, status_code=status.HTTP_201_CREATED)
async def create_sale_order(
    order_in: SaleOrderCreate,
    background_tasks: BackgroundTasks,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_active_customer),
):
    order_in.creator_id = str(current_user["_id"])
    new_order = await sale_order.create(db, obj_in=order_in)

    background_tasks.add_task(run_matching_cycle, db, str(new_order["_id"]), "sale")
    
    # You would also add agent linking and notification logic here as in the purchase order endpoint.
    return new_order

@router.put("/orders/sale/{order_id}", response_model=SaleOrderInDB)
async def update_sale_order(
    order_id: str,
    update_data: Dict[str, Any],
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    order = await sale_order.get(db, id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Sale order not found")
    if order["creator_id"] != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="Not authorized to update this order")
        
    updated_order = await sale_order.update(db, db_obj=order, obj_in=update_data)
    return updated_order

@router.delete("/orders/sale/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sale_order(
    order_id: str,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    order = await sale_order.get(db, id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Sale order not found")
    if order["creator_id"] != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="Not authorized to delete this order")
    
    await sale_order.remove(db, id=order_id)
    return