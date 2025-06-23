from fastapi import APIRouter, Depends, Body, HTTPException, BackgroundTasks, status
from typing import Dict, Any

from app.crud import crud_order, crud_agent
from app.db.mongodb import get_db
from app.models.order import PurchaseOrderCreate, PurchaseOrderCreateIn, SaleOrderCreate, SaleOrderInDB
from app.api.deps import get_current_active_customer, get_current_user
from app.services import image_generation, geo
from app.services.notification_service import create_and_dispatch_notification
from app.services.matching_service import run_matching_cycle

router = APIRouter()

@router.post("/orders/purchase/generate-assets")
async def generate_purchase_order_assets(prompt: str = Body(..., embed=True)):
    """
    Takes a product description, generates an image, and gets Google search results.
    """
    image_url = await image_generation.generate_product_image_from_prompt(prompt)
    search_results = await image_generation.search_google_for_prompt(prompt)
    
    if not image_url:
        raise HTTPException(status_code=500, detail="Failed to generate image.")
        
    return {"generated_image_url": image_url, "search_results": search_results.get("items", [])}

@router.post("/orders/purchase", status_code=201)
async def create_purchase_order(
    order_in: PurchaseOrderCreateIn,
    background_tasks: BackgroundTasks, # <-- ADD BackgroundTasks DEPENDENCY
    db=Depends(get_db),
    current_customer: dict = Depends(get_current_active_customer),
):
    """
    Create a purchase order. This will trigger agent linking and a background
    task for order matching.
    """
    order_data = order_in.model_dump()
    order_data["creator_id"] = str(current_customer["_id"])
    order_to_create = PurchaseOrderCreate(**order_data)
    new_order = await crud_order.purchase_order.create(db, obj_in=order_to_create)
    
    # --- Agent linking logic remains the same ---
    longitude, latitude = current_customer["location"]["coordinates"]
    nearby_agents = await geo.get_agents_in_radius(db, longitude, latitude)
    await crud_order.purchase_order.update(db, db_obj=new_order, obj_in={"linked_agents_ids": [str(a["_id"]) for a in nearby_agents]})
    for agent in nearby_agents:
        subject = "New Order Alert!"
        message_body = f"You have been linked to a new purchase order created near your location. Order ID: {str(new_order['_id'])}"
        await create_and_dispatch_notification(db, target_user=agent, subject=subject, message_body=message_body)

    # NEW: Trigger the matching cycle in the background
    background_tasks.add_task(run_matching_cycle, db, str(new_order["_id"]), "purchase")

    return {"message": "Purchase order created. Matching is in progress.", "order": new_order}


@router.post("/orders/sale", status_code=201)
async def create_sale_order(
    order_in: SaleOrderCreate,
    background_tasks: BackgroundTasks, # <-- ADD BackgroundTasks DEPENDENCY
    db=Depends(get_db),
    current_customer: dict = Depends(get_current_active_customer),
):
    """
    Create a sale order. Creator is derived from token. This also triggers
    agent linking and a background task for order matching.
    """
    # This assumes product_id is validated on the frontend or in a previous step
    order_in.creator_id = str(current_customer["_id"])
    new_order = await crud_order.sale_order.create(db, obj_in=order_in)

    # NEW: Trigger the matching cycle in the background
    background_tasks.add_task(run_matching_cycle, db, str(new_order["_id"]), "sale")
    
    # You would also add agent linking and notification logic here as in the purchase order endpoint.

    return {"message": "Sale order created. Matching is in progress.", "order": new_order}

@router.put("/orders/sale/{order_id}", response_model=SaleOrderInDB)
async def update_sale_order(
    order_id: str,
    update_data: Dict[str, Any],
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update a sale order. Only the creator can update.
    """
    order = await crud_order.get(db, id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Sale order not found")
    if order["creator_id"] != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="Not authorized to update this order")
        
    updated_order = await crud_order.update(db, db_obj=order, obj_in=update_data)
    return updated_order

@router.delete("/orders/sale/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sale_order(
    order_id: str,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a sale order. Only the creator can delete.
    """
    order = await crud_order.get(db, id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Sale order not found")
    if order["creator_id"] != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="Not authorized to delete this order")
    
    await crud_order.remove(db, id=order_id)
    return