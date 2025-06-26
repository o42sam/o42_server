from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import List, Dict, Any

from app.api.deps import get_current_active_customer
from app.db.mongodb import get_db
from app.models.product import ProductCreate, ProductInDB, ProductAnalysisResponse
from app.crud import product as crud_product
from app.services import media_analysis_service
router = APIRouter()

@router.post("/products", response_model=ProductInDB, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_in: ProductCreate,
    db=Depends(get_db),
    # Any active customer can create a product to sell
    current_user: dict = Depends(get_current_active_customer)
):
    """
    Create a new product listing.
    """
    created_product = await crud_product.create(db, obj_in=product_in)
    return created_product

@router.get("/products/{product_id}", response_model=ProductInDB)
async def get_product(product_id: str, db=Depends(get_db)):
    """
    Get a single product by its ID.
    """
    product = await crud_product.get(db, id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.put("/products/{product_id}", response_model=ProductInDB)
async def update_product(
    product_id: str,
    update_data: Dict[str, Any],
    db=Depends(get_db),
    current_user: dict = Depends(get_current_active_customer)
):
    """
    Update a product. A user can only update a product they created.
    (Note: Ownership check is simplified here. In a real app, products would have an owner_id)
    """
    product = await crud_product.get(db, id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Simple ownership check - can be enhanced by adding owner_id to product model
    # For now, any authenticated customer can update, which should be tightened.
    
    updated_product = await crud_product.update(db, db_obj=product, obj_in=update_data)
    return updated_product

@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_active_customer)
):
    """
    Delete a product.
    """
    product = await crud_product.get(db, id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    await crud_product.remove(db, id=product_id)
    return

@router.post("/products/analyze-image", response_model=ProductAnalysisResponse)
async def analyze_product_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_active_customer)
):
    """
    Upload a product image to automatically generate a name, description,
    and suggested category.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image.")
    
    media_bytes = await file.read()
    
    try:
        # Get name, description, and keywords from the Vision model
        product_details = await media_analysis_service.generate_product_details_from_media(
            media_bytes, file.content_type
        )
        
        # Use the generated text to find the best category
        text_for_categorization = f"{product_details['name']} {' '.join(product_details['keywords'])}"
        suggested_category = media_analysis_service.find_best_category(text_for_categorization)
        
        return {
            "name": product_details["name"],
            "description": product_details["description"],
            "suggested_category": suggested_category
        }
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/products/analyze-video", response_model=ProductAnalysisResponse)
async def analyze_product_video(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_active_customer)
):
    """
    Upload a product video. A frame will be extracted and analyzed to generate
    a name, description, and suggested category.
    """
    if not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a video.")
    
    video_bytes = await file.read()
    
    try:
        # Extract a representative frame from the video
        frame_bytes = media_analysis_service.extract_frame_from_video(video_bytes)
        
        # Analyze the extracted frame (pass as JPEG)
        product_details = await media_analysis_service.generate_product_details_from_media(
            frame_bytes, "image/jpeg"
        )
        
        # Use the generated text to find the best category
        text_for_categorization = f"{product_details['name']} {' '.join(product_details['keywords'])}"
        suggested_category = media_analysis_service.find_best_category(text_for_categorization)
        
        return {
            "name": product_details["name"],
            "description": product_details["description"],
            "suggested_category": suggested_category
        }
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))