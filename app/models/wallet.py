from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class WalletBase(BaseModel):
    owner_id: str
    balance: float = 0.0

class WalletCreate(WalletBase):
    pass

class WalletInDB(WalletBase):
    id: str = Field(..., alias="_id")
    paystack_account_id: Optional[str] = None
    restrictions: List[str] = []
    created: datetime = Field(default_factory=datetime.utcnow)
    lastUpdated: datetime = Field(default_factory=datetime.utcnow)

class Transaction(BaseModel):
    id: str = Field(..., alias="_id")
    order_id: str
    buyer_id: str
    seller_id: str
    agent_id: str
    amount: float
    app_fee: float
    agent_commission: float
    seller_amount: float
    created: datetime = Field(default_factory=datetime.utcnow)
    lastUpdated: datetime = Field(default_factory=datetime.utcnow)

class WithdrawalRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Amount to withdraw in NGN")
    account_number: str = Field(..., description="Destination bank account number")
    bank_code: str = Field(..., description="Paystack code for the destination bank")
    two_fa_code: str = Field(..., min_length=6, max_length=6, description="6-digit 2FA code from authenticator app")

class WalletUpdate(BaseModel):
    """Defines fields that can be updated for a Wallet (admin-only)."""
    balance: Optional[float] = None
    restrictions: Optional[List[str]] = None