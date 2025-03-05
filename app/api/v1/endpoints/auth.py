import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.api.v1.schemas.token import Token

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncIOMotorClient = Depends(get_db)):
    logger.info(f"Login attempt for email: {form_data.username}")
    user = await db.o42.agents.find_one({"email": form_data.username}) or await db.o42.customers.find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user_id = str(user["_id"])
    access_token = create_access_token({"sub": user_id})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
async def logout():
    logger.info("User logged out")
    # JWT is stateless; client should discard token
    return {"message": "Logged out successfully"}