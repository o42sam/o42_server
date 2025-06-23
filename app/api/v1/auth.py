from fastapi import APIRouter, Depends, HTTPException, Body, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

from app.core import security
from app.core.config import settings
from app.db.mongodb import get_db
from app.crud import customer, agent # <-- Corrected imports
from app.models import token as token_model
from app.api.deps import get_current_user # <-- Corrected import

router = APIRouter()

@router.post("/auth/login", response_model=token_model.Token)
async def login(
    db=Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    user = await customer.get_by_email(db, email=form_data.username)
    if not user:
        user = await agent.get_by_email(db, email=form_data.username)

    if not user or not security.verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=str(user["_id"]), expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/auth/2fa/setup")
async def setup_2fa(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    if current_user.get("two_fa_secret"):
        raise HTTPException(status_code=400, detail="2FA is already enabled.")

    secret = security.generate_2fa_secret()
    
    user_crud = agent if current_user["user_type"] == "agent" else customer
    await user_crud.update(db, db_obj=current_user, obj_in={"two_fa_secret": secret})

    return {
        "message": "2FA setup initiated. Scan the QR code with your authenticator app.",
        "uri": security.get_2fa_uri(current_user["email"], secret)
    }

# This endpoint was missing from the file I gave you, but may be needed later.
@router.post("/auth/2fa/verify-login")
async def verify_2fa_login(
    db=Depends(get_db), 
    email: str = Body(...),
    password: str = Body(...),
    code: str = Body(...)
):
    user = await customer.get_by_email(db, email=email)
    if not user:
        user = await agent.get_by_email(db, email=email)
    
    if not user or not user.get("two_fa_secret") or not security.verify_password(password, user["hashed_password"]):
         raise HTTPException(status_code=400, detail="Invalid credentials or 2FA not enabled")

    if not security.verify_2fa_code(user["two_fa_secret"], code):
        raise HTTPException(status_code=400, detail="Invalid 2FA code")
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=str(user["_id"]), expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}