from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

from app.core import security
from app.core.config import settings
from app.db.mongodb import get_db
from app.crud import crud_customer, crud_agent
from app.models import token as token_model
from app.api.deps import get_current_user

router = APIRouter()

@router.post("/auth/login", response_model=token_model.Token)
async def login(
    db=Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user = await crud_customer.customer.get_by_email(db, email=form_data.username)
    if not user:
        user = await crud_agent.agent.get_by_email(db, email=form_data.username)

    if not user or not security.verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    if not user["isEmailVerified"]:
         raise HTTPException(status_code=400, detail="Email not verified")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=str(user["_id"]), expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/auth/2fa/setup")
async def setup_2fa(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    """Generate and store a 2FA secret, return the provisioning URI."""
    if current_user.get("two_fa_secret"):
        raise HTTPException(status_code=400, detail="2FA is already enabled.")

    secret = security.generate_2fa_secret()
    
    user_crud = crud_agent.agent if current_user["user_type"] == "agent" else crud_customer.customer
    await user_crud.update(db, db_obj=current_user, obj_in={"two_fa_secret": secret})

    return {
        "message": "2FA setup initiated. Scan the QR code with your authenticator app.",
        "secret": secret,
        "uri": security.get_2fa_uri(current_user["email"], secret)
    }

@router.post("/auth/2fa/verify-login")
async def verify_2fa_login(
    db=Depends(get_db), 
    email: str = Body(...),
    password: str = Body(...),
    code: str = Body(...)
):
    """Login for a user with 2FA enabled."""
    user = await crud_customer.customer.get_by_email(db, email=email)
    if not user:
        user = await crud_agent.agent.get_by_email(db, email=email)
    
    if not user or not user.get("two_fa_secret") or not security.verify_password(password, user["hashed_password"]):
         raise HTTPException(status_code=400, detail="Invalid credentials or 2FA not enabled")

    if not security.verify_2fa_code(user["two_fa_secret"], code):
        raise HTTPException(status_code=400, detail="Invalid 2FA code")
        

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=str(user["_id"]), expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}