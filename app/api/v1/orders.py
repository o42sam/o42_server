from fastapi import APIRouter, Depends, Body, HTTPException
from typing import Dict, Any

from app.crud import crud_order, crud_agent
from app.db.mongodb import get_db
from app.models.order import PurchaseOrderCreate, PurchaseOrderCreateIn, SaleOrderCreate 
from app.api.deps import get_current_active_customer
from app.services import image_generation, geo
from app.services.notification_service import create_and_dispatch_notification

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
    db=Depends(get_db),
    current_customer: dict = Depends(get_current_active_customer),
):
    """
    Create a purchase order. The creator is derived from the auth token.
    """


    order_data = order_in.model_dump()
    

    order_data["creator_id"] = str(current_customer["_id"])


    order_to_create = PurchaseOrderCreate(**order_data)
    

    new_order = await crud_order.purchase_order.create(db, obj_in=order_to_create)
    

    

    longitude, latitude = current_customer["location"]["coordinates"]
    nearby_agents = await geo.get_agents_in_radius(db, longitude, latitude)
    
    await crud_order.purchase_order.update(db, db_obj=new_order, obj_in={"linked_agents_ids": [str(a["_id"]) for a in nearby_agents]})
    

    for agent in nearby_agents:
        subject = "New Order Alert!"
        message_body = f"You have been linked to a new purchase order created near your location. Order ID: {str(new_order['_id'])}"
        await create_and_dispatch_notification(db, target_user=agent, subject=subject, message_body=message_body)

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






    order_in.creator_id = str(current_customer["_id"])
    new_order = await crud_order.sale_order.create(db, obj_in=order_in)

    
    return {"message": "Sale order created.", "order": new_order}