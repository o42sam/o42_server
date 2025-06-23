from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any

from app.api.deps import get_current_active_customer
from app.db.mongodb import get_db
from app.models.product import ProductCreate, ProductInDB
from app.crud import product as crud_product

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