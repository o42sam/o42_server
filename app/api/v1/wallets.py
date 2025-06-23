from fastapi import APIRouter, Depends, HTTPException, Body, status

from app.api.deps import get_current_user, get_current_active_customer, get_current_active_agent
from app.crud import crud_wallet, crud_order
from app.db.mongodb import get_db
from app.models.wallet import WalletInDB
from app.core.security import verify_2fa_code
from app.services import payment_service, notification_service
from app.core.config import settings

router = APIRouter()

@router.get("/wallets/me", response_model=WalletInDB)
async def read_my_wallet(
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Retrieve the current user's wallet.
    """
    wallet = await crud_wallet.wallet.get_by_owner_id(db, owner_id=str(current_user["_id"]))
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found for this user.")
    return wallet

@router.post("/wallets/withdraw")
async def request_withdrawal(
    db=Depends(get_db),
    amount: float = Body(..., gt=0),
    two_fa_code: str = Body(..., description="2FA code from authenticator app"),
    current_agent: dict = Depends(get_current_active_agent)
):
    """
    Request a withdrawal from the agent's wallet. Requires 2FA.
    """

    if not current_agent.get("two_fa_secret") or not verify_2fa_code(current_agent["two_fa_secret"], two_fa_code):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid 2FA code.")


    wallet = await crud_wallet.wallet.get_by_owner_id(db, owner_id=str(current_agent["_id"]))
    if not wallet or wallet["balance"] < amount:
        raise HTTPException(status_code=400, detail="Insufficient wallet balance.")
        










    new_balance = wallet["balance"] - amount
    await crud_wallet.wallet.update(db, db_obj=wallet, obj_in={"balance": new_balance})

    return {"message": "Withdrawal request received and is being processed.", "new_balance": new_balance}