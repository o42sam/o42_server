from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from motor.motor_asyncio import AsyncIOMotorDatabase
import redis.asyncio as redis

from app.core.config import settings
from app.db.mongodb import get_db
from app.db.redis_client import get_redis
from app.models import token as token_model
from app.models import customer as customer_model
from app.models import agent as agent_model
from app.crud import crud_customer, crud_agent

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

async def get_current_user(
    db: AsyncIOMotorDatabase = Depends(get_db), token: str = Security(reusable_oauth2)
) -> dict:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = token_model.TokenData(id=payload.get("sub"))
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
        
    # Check both customer and agent collections
    user = await crud_customer.customer.get(db, id=token_data.id)
    if user:
        user["user_type"] = "customer"
        return user

    user = await crud_agent.agent.get(db, id=token_data.id)
    if user:
        user["user_type"] = "agent"
        return user
        
    raise HTTPException(status_code=404, detail="User not found")

def get_current_active_customer(
    current_user: dict = Depends(get_current_user)
) -> dict:
    if current_user.get("user_type") != "customer":
         raise HTTPException(status_code=403, detail="Not a customer")
    if not current_user.get("isEmailVerified"):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_current_active_agent(
    current_user: dict = Depends(get_current_user)
) -> dict:
    if current_user.get("user_type") != "agent":
         raise HTTPException(status_code=403, detail="Not an agent")
    if not current_user.get("isEmailVerified"):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user