from fastapi import APIRouter, Depends, HTTPException
from app.crud import customer as crud_customer # <-- Use aliased import for clarity
from app.db.mongodb import get_db
from app.models.customer import CustomerCreate, CustomerInDB, CustomerUpdate, CustomerRegisterOut 
from app.core.security import get_password_hash
from app.api.deps import get_current_active_customer, get_current_user

router = APIRouter()

@router.post("/customers/register", response_model=CustomerRegisterOut)
async def register_customer(
    customer_in: CustomerCreate,
    db = Depends(get_db)
):
    customer = await crud_customer.get_by_email(db, email=customer_in.email)
    if customer:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists.",
        )
    hashed_password = get_password_hash(customer_in.password)
    # Create a partial DB object
    db_customer_data = {
        "email": customer_in.email, 
        "hashed_password": hashed_password, 
        "isEmailVerified": False
    }
    
    # We cannot use the default CRUD create if the model has required fields.
    # We will insert directly and then fetch.
    result = await db.customers.insert_one(db_customer_data)
    created_customer = await db.customers.find_one({"_id": result.inserted_id})

    # Manually construct the response to match the response_model
    return {
        "id": str(created_customer["_id"]),
        "email": created_customer["email"],
        "isEmailVerified": created_customer.get("isEmailVerified", False)
    }

@router.get("/customers/me", response_model=CustomerInDB)
def read_customer_me(current_customer: dict = Depends(get_current_user)):
    """
    Get current customer's profile.
    """
    return current_customer

@router.put("/customers/me", response_model=CustomerInDB)
async def update_customer_me(
    customer_in: CustomerUpdate,
    db = Depends(get_db),
    current_customer: dict = Depends(get_current_user),
):
    """
    Update current customer's profile.
    """
    updated_customer = await crud_customer.update(
        db, db_obj=current_customer, obj_in=customer_in
    )
    return updated_customer