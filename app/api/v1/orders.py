from fastapi import APIRouter, Depends, Body, HTTPException
from typing import Dict, Any

from app.crud import crud_order, crud_agent
from app.db.mongodb import get_db
from app.models.order import PurchaseOrderCreate, SaleOrderCreate
from app.api.deps import get_current_active_customer
from app.services import image_generation, geo, notification_service

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
    order_in: PurchaseOrderCreate,
    db=Depends(get_db),
    current_customer: dict = Depends(get_current_active_customer),
):
    """
    Create a purchase order. This will trigger matching and agent linking.
    """
    # Create the purchase order
    order_in.creator_id = str(current_customer["_id"])
    new_order = await crud_order.purchase_order.create(db, obj_in=order_in)
    
    # In a real app, this would be a background task
    # Find and link nearby agents
    longitude, latitude = current_customer["location"]["coordinates"]
    nearby_agents = await geo.get_agents_in_radius(db, longitude, latitude)
    agent_ids = [str(agent["_id"]) for agent in nearby_agents]
    
    await crud_order.purchase_order.update(db, db_obj=new_order, obj_in={"linked_agents_ids": agent_ids})
    
    # Notify linked agents
    for agent_id in agent_ids:
        # Create DB notification
        # Send SMS/Email
        agent = await crud_agent.agent.get(db, id=agent_id)
        if agent and agent.get("phone_number"):
            await notification_service.send_sms(agent["phone_number"], "You've been linked to a new purchase order!")

    # Here you would also trigger matching logic against sale orders
    
    return {"message": "Purchase order created and agents notified.", "order": new_order}

@router.post("/orders/sale", status_code=201)
async def create_sale_order(
    order_in: SaleOrderCreate,
    db=Depends(get_db),
    current_customer: dict = Depends(get_current_active_customer),
):
    """
    Create a sale order. This will trigger matching and agent linking.
    """
    # Similar logic to purchase order creation:
    # 1. Set creator_id
    # 2. Create the order
    # 3. Link agents via geo-query (as a background task)
    # 4. Notify agents
    # 5. Trigger matching logic against purchase orders
    order_in.creator_id = str(current_customer["_id"])
    new_order = await crud_order.sale_order.create(db, obj_in=order_in)
    # ... remaining logic ...
    
    return {"message": "Sale order created.", "order": new_order}