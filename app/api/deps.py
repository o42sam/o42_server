from fastapi import Depends, HTTPException, status, Security, Query
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.db.mongodb import get_db
from app.models import token as token_model
from app.crud import customer, agent, admin as crud_admin

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

async def get_current_user(
    db: AsyncIOMotorDatabase = Depends(get_db), token: str = Security(reusable_oauth2)
) -> dict:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=["HS256"]
        )
        token_data = token_model.TokenData(id=payload.get("sub"))
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    user_doc = await customer.get(db, id=token_data.id)
    if user_doc:
        user_doc["user_type"] = "customer"
        return user_doc

    user_doc = await agent.get(db, id=token_data.id)
    if user_doc:
        user_doc["user_type"] = "agent"
        return user_doc
        
    raise HTTPException(status_code=404, detail="User not found")

def get_current_active_user(current_user: dict = Depends(get_current_user)):
    # This dependency can be used for actions that require a verified account
    if not current_user.get("isEmailVerified"):
        raise HTTPException(status_code=400, detail="User's email is not verified")
    return current_user

def get_current_active_customer(current_user: dict = Depends(get_current_user)):
    if current_user.get("user_type") != "customer":
         raise HTTPException(status_code=403, detail="Not a customer")
    if not current_user.get("isEmailVerified"):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_current_active_agent(current_user: dict = Depends(get_current_user)):
    if current_user.get("user_type") != "agent":
         raise HTTPException(status_code=403, detail="Not an agent")
    if not current_user.get("isEmailVerified"):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_user_from_query(
    token: str = Query(...),
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> dict:
    # This is correct as is, no changes needed
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        token_data = token_model.TokenData(id=payload.get("sub"))
    except (JWTError, ValidationError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate credentials from token")
    user = await customer.get(db, id=token_data.id)
    if user:
        user["user_type"] = "customer"
        return user
    user = await agent.get(db, id=token_data.id)
    if user:
        user["user_type"] = "agent"
        return user
    raise HTTPException(status_code=404, detail="User not found")

async def get_current_admin(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> dict:
    """
    Dependency to ensure the current user is an admin.
    Raises a 403 Forbidden error if not.
    """
    # We check if a user with the same ID exists in the admins collection.
    # This is a simple way to grant admin privileges.
    admin_user = await db.admins.find_one({"_id": current_user["_id"]})
    if not admin_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have sufficient privileges."
        )
    return admin_user