import logging
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.database import get_db
from app.core.security import get_current_user, hash_password
from app.models.customer import Customer, CustomerCreate, CustomerUpdate
from app.services.email import send_verification_email
from app.utils.helpers import generate_verification_code
from bson import ObjectId

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=Customer)
async def create_customer(customer_data: CustomerCreate, db: AsyncIOMotorClient = Depends(get_db)):
    logger.info(f"Creating customer with email: {customer_data.email}")
    if await db.o42.customers.find_one({"email": customer_data.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = hash_password(customer_data.password)
    customer_dict = customer_data.dict(exclude={"password"})
    customer_dict["password"] = hashed_password
    result = await db.o42.customers.insert_one(customer_dict)
    customer_id = str(result.inserted_id)
    customer_dict["id"] = customer_id

    email_code = generate_verification_code()
    await db.o42.verification_codes.insert_one({
        "user_id": customer_id, "code": email_code, "type": "email",
        "created_at": customer_dict["created_at"], "expires_at": customer_dict["created_at"] + timedelta(minutes=15)
    })
    await send_verification_email(customer_data.email, email_code)
    return Customer(**customer_dict)

@router.get("/{customer_id}", response_model=Customer)
async def read_customer(customer_id: str, db: AsyncIOMotorClient = Depends(get_db), current_user: Customer = Depends(get_current_user)):
    logger.info(f"Fetching customer: {customer_id}")
    customer = await db.o42.customers.find_one({"_id": ObjectId(customer_id)})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    customer["id"] = str(customer["_id"])
    return Customer(**customer)

@router.put("/{customer_id}", response_model=Customer)
async def update_customer(
    customer_id: str,
    customer_update: CustomerUpdate,
    db: AsyncIOMotorClient = Depends(get_db),
    current_user: Customer = Depends(get_current_user)
):
    logger.info(f"Updating customer: {customer_id}")
    if str(current_user.id) != customer_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    update_data = {k: v for k, v in customer_update.dict(exclude_unset=True).items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    result = await db.o42.customers.update_one({"_id": ObjectId(customer_id)}, {"$set": update_data})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found or no changes made")
    customer = await db.o42.customers.find_one({"_id": ObjectId(customer_id)})
    customer["id"] = str(customer["_id"])
    return Customer(**customer)

@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(customer_id: str, db: AsyncIOMotorClient = Depends(get_db), current_user: Customer = Depends(get_current_user)):
    logger.info(f"Deleting customer: {customer_id}")
    if str(current_user.id) != customer_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    result = await db.o42.customers.delete_one({"_id": ObjectId(customer_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")