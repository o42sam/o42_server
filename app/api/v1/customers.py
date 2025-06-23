from fastapi import APIRouter, Depends, HTTPException

from app.crud import crud_customer
from app.db.mongodb import get_db
from app.models.customer import CustomerCreate, CustomerInDB, CustomerUpdate
from app.core.security import get_password_hash
from app.api.deps import get_current_active_customer

router = APIRouter()

@router.post("/customers/register", response_model=CustomerInDB)
async def register_customer(
    customer_in: CustomerCreate,
    db = Depends(get_db)
):
    """
    Create a new customer (Step 1: email and password).
    """
    customer = await crud_customer.customer.get_by_email(db, email=customer_in.email)
    if customer:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists.",
        )
    hashed_password = get_password_hash(customer_in.password)
    db_customer = {"email": customer_in.email, "hashed_password": hashed_password}
    created_customer = await crud_customer.customer.create(db, obj_in=db_customer)

    return created_customer

@router.get("/customers/me", response_model=CustomerInDB)
def read_customer_me(current_customer: dict = Depends(get_current_active_customer)):
    """
    Get current customer's profile.
    """
    return current_customer

@router.put("/customers/me", response_model=CustomerInDB)
async def update_customer_me(
    customer_in: CustomerUpdate,
    db = Depends(get_db),
    current_customer: dict = Depends(get_current_active_customer),
):
    """
    Update current customer's profile.
    """
    updated_customer = await crud_customer.customer.update(
        db, db_obj=current_customer, obj_in=customer_in
    )
    return updated_customer