# app/api/v1/reviews.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any

from app.api.deps import get_current_active_customer, get_current_user
from app.db.mongodb import get_db
from app.models.review import ReviewCreate, ReviewInDB
from app.crud import review as crud_review

router = APIRouter()

@router.post("/reviews", response_model=ReviewInDB, status_code=status.HTTP_201_CREATED)
async def create_review(
    review_in: ReviewCreate,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_active_customer)
):
    """
    Create a new review for an agent. The author is the current customer.
    """
    review_in.author_id = str(current_user["_id"])
    created_review = await crud_review.create(db, obj_in=review_in)
    return created_review

@router.get("/agents/{agent_id}/reviews", response_model=List[ReviewInDB])
async def get_reviews_for_agent(agent_id: str, db=Depends(get_db)):
    """
    Get all reviews for a specific agent.
    """
    reviews = await db.reviews.find({"target_agent_id": agent_id}).to_list(length=None)
    return reviews

@router.put("/reviews/{review_id}", response_model=ReviewInDB)
async def update_review(
    review_id: str,
    update_data: Dict[str, Any],
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update a review. Only the original author can update their review.
    """
    review = await crud_review.get(db, id=review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review["author_id"] != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="Not authorized to update this review")
        
    updated_review = await crud_review.update(db, db_obj=review, obj_in=update_data)
    return updated_review

@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: str,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a review. Only the original author can delete their review.
    """
    review = await crud_review.get(db, id=review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review["author_id"] != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="Not authorized to delete this review")
        
    await crud_review.remove(db, id=review_id)
    return