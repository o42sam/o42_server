from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.crud import wallet as crud_wallet, customer as crud_customer, agent as crud_agent
from app.db.mongodb import get_db
from app.models.wallet import WalletCreate, WalletInDB, WithdrawalRequest
from app.services import payment_service
from app.core import security 

router = APIRouter()

@router.post("/wallets", response_model=WalletInDB, status_code=status.HTTP_201_CREATED)
async def create_wallet(
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new wallet for the authenticated user.
    A user can only have one wallet at a time.
    This also creates a dedicated virtual account via Paystack.
    """
    user_id = str(current_user["_id"])

    # 1. Check if a wallet already exists for this user
    existing_wallet = await crud_wallet.get_by_owner_id(db, owner_id=user_id)
    if existing_wallet:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A wallet already exists for this user."
        )

    # 2. Create a customer on Paystack and a dedicated virtual account (DVA)
    try:
        # Note: Paystack's create customer is idempotent, it won't create duplicates for the same email.
        ps_customer = await payment_service.create_customer(
            email=current_user["email"],
            first_name=current_user.get("fName", "User"),
            last_name=current_user.get("lName", str(current_user["_id"])),
            phone=current_user.get("phone_number", "")
        )

        dva_data = await payment_service.create_dedicated_virtual_account(
            customer_code=ps_customer["customer_code"]
        )
        # The DVA number is what the user will pay into. We store it as the wallet's unique account ID.
        paystack_account_id = dva_data.get("account_number")
        
        if not paystack_account_id:
             raise Exception("Failed to retrieve account number from payment service.")

    except Exception as e:
        # If any Paystack operation fails, we should not create the wallet in our DB.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Payment service provider error: {e}"
        )

    # 3. Create the wallet in our database
    wallet_in = WalletCreate(
        owner_id=user_id,
        balance=0.0 # Wallets start with a zero balance
    )
    # The CRUD create method now needs to be updated to accept the Paystack ID
    new_wallet = await crud_wallet.create(db, obj_in=wallet_in, paystack_id=paystack_account_id)
    
    # 4. Link the new wallet ID back to the user's document
    user_crud = crud_agent if current_user["user_type"] == "agent" else crud_customer
    await user_crud.update(db, db_obj=current_user, obj_in={"wallet_id": str(new_wallet["_id"])})

    return new_wallet

@router.get("/wallets/me", response_model=WalletInDB)
async def read_my_wallet(
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Retrieve the current authenticated user's wallet.
    """
    wallet = await crud_wallet.get_by_owner_id(db, owner_id=str(current_user["_id"]))
    if not wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found for this user.")
    return wallet

@router.delete("/wallets/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_wallet(
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete the current authenticated user's wallet.
    """
    user_id = str(current_user["_id"])

    # 1. Find the wallet to get its ID for deletion
    wallet_to_delete = await crud_wallet.get_by_owner_id(db, owner_id=user_id)
    if not wallet_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No wallet found for this user to delete."
        )

    # 2. Remove the wallet from the wallets collection
    await crud_wallet.remove(db, id=str(wallet_to_delete["_id"]))
    
    # 3. Unlink the wallet from the user document by setting wallet_id to None
    user_crud = crud_agent if current_user["user_type"] == "agent" else crud_customer
    await user_crud.update(db, db_obj=current_user, obj_in={"wallet_id": None})
    
    # In a real-world scenario, you might also want to deactivate the DVA on Paystack.
    
    return

@router.post("/wallets/withdraw")
async def request_withdrawal(
    request_data: WithdrawalRequest,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Withdraw funds from a user's wallet to their Nigerian bank account.
    This operation is protected by Two-Factor Authentication (2FA).
    """
    user_id = str(current_user["_id"])

    # 1. Security Check: Verify 2FA code
    two_fa_secret = current_user.get("two_fa_secret")
    if not two_fa_secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="2FA is not enabled for this account. Please set it up before withdrawing."
        )
    if not security.verify_2fa_code(two_fa_secret, request_data.two_fa_code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid 2FA code."
        )

    # 2. Wallet & Balance Check
    wallet = await crud_wallet.get_by_owner_id(db, owner_id=user_id)
    if not wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found for this user.")
    if wallet["balance"] < request_data.amount:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient wallet balance.")

    # 3. Paystack Transfer Flow
    try:
        # Step 3a: Create a transfer recipient on Paystack. This validates the account details.
        recipient_data = await payment_service.create_transfer_recipient(
            name=f"{current_user.get('fName')} {current_user.get('lName')}",
            account_number=request_data.account_number,
            bank_code=request_data.bank_code
        )
        recipient_code = recipient_data.get("recipient_code")

        if not recipient_code:
            raise Exception("Failed to create transfer recipient with payment provider.")

        # Step 3b: Initiate the transfer to the newly created recipient
        amount_in_kobo = int(request_data.amount * 100)
        transfer_data = await payment_service.initiate_transfer(
            amount_kobo=amount_in_kobo,
            recipient_code=recipient_code,
            reason="o42 Marketplace Wallet Withdrawal"
        )
        
        if transfer_data.get("status") != "success" and transfer_data.get("status") != "pending":
            raise Exception(f"Transfer initiation failed: {transfer_data.get('message')}")

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Payment service provider error: {e}"
        )

    # 4. Update Wallet Balance in our Database
    # This should only happen AFTER the transfer has been successfully initiated.
    new_balance = wallet["balance"] - request_data.amount
    updated_wallet = await crud_wallet.update(db, db_obj=wallet, obj_in={"balance": new_balance})

    # Note: For a production system, you should also log this transaction in your `transactions` collection
    # for auditing and record-keeping purposes.

    return {
        "message": "Withdrawal initiated successfully. The transfer is being processed.",
        "transfer_status": transfer_data.get("status"),
        "new_balance": updated_wallet["balance"]
    }