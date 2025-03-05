import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.database import get_db
from app.core.security import get_current_user
from app.services.face_verification import verify_face
from datetime import datetime
from bson import ObjectId

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/verify-email")
async def verify_email(email: str, code: str, db: AsyncIOMotorClient = Depends(get_db)):
    logger.info(f"Verifying email: {email}")
    verification = await db.o42.verification_codes.find_one({"type": "email", "code": code})
    if not verification or verification["expires_at"] < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    user = await db.o42.agents.find_one({"_id": ObjectId(verification["user_id"])}) or await db.o42.customers.find_one({"_id": ObjectId(verification["user_id"])})
    if not user or user["email"] != email:
        raise HTTPException(status_code=400, detail="Email mismatch")
    await db.o42.agents.update_one({"_id": ObjectId(verification["user_id"])}, {"$set": {"email_verified": True}}) or \
        await db.o42.customers.update_one({"_id": ObjectId(verification["user_id"])}, {"$set": {"email_verified": True}})
    await db.o42.verification_codes.delete_one({"_id": verification["_id"]})
    return {"message": "Email verified"}

@router.post("/verify-phone")
async def verify_phone(phone_number: str, code: str, db: AsyncIOMotorClient = Depends(get_db)):
    logger.info(f"Verifying phone: {phone_number}")
    verification = await db.o42.verification_codes.find_one({"type": "phone", "code": code})
    if not verification or verification["expires_at"] < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    user = await db.o42.agents.find_one({"_id": ObjectId(verification["user_id"])})
    if not user or user["phone_number"] != phone_number:
        raise HTTPException(status_code=400, detail="Phone number mismatch")
    await db.o42.agents.update_one({"_id": ObjectId(verification["user_id"])}, {"$set": {"phone_verified": True}})
    await db.o42.verification_codes.delete_one({"_id": verification["_id"]})
    return {"message": "Phone verified"}

@router.post("/verify-photo")
async def verify_photo(
    photo: UploadFile = File(...),
    db: AsyncIOMotorClient = Depends(get_db),
    current_user: Agent = Depends(get_current_user)
):
    logger.info(f"Verifying photo for agent: {current_user.id}")
    photo_path = f"uploads/{photo.filename}"
    with open(photo_path, "wb") as f:
        f.write(await photo.read())
    match = await verify_face(current_user.id, photo_path)
    if not match:
        raise HTTPException(status_code=400, detail="Face verification failed")
    return {"message": "Face verified successfully"}