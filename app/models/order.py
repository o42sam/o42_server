from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime
from enum import Enum

class SaleType(str, Enum):
    fixed_price = "fixed-price"
    auction = "auction"
    negotiation = "negotiation"


class SaleOrderBase(BaseModel):
    creator_id: str
    product_id: str
    sale_type: SaleType
    price: float
    commission_percentage: float = Field(..., ge=0, le=100)
    location: Any

class SaleOrderCreate(SaleOrderBase):
    pass

class SaleOrderInDB(SaleOrderBase):
    id: str = Field(..., alias="_id")
    linked_agents_ids: List[str] = []
    delivering_agent_id: Optional[str] = None
    isDelivered: bool = False
    matching_purchase_orders: List[Dict[str, Any]] = []
    created: datetime = Field(default_factory=datetime.utcnow)
    lastUpdated: datetime = Field(default_factory=datetime.utcnow)


class PurchaseOrderBase(BaseModel):
    creator_id: str
    product_description: str
    product_image: str

class PurchaseOrderCreateIn(BaseModel):
    """Model for data coming IN from the client. Does not include creator_id."""
    product_description: str
    product_image: str

class PurchaseOrderCreate(PurchaseOrderBase):
    """Internal model used for creating the DB record. Includes server-set creator_id."""
    pass

class PurchaseOrderInDB(PurchaseOrderBase):
    id: str = Field(..., alias="_id")
    matching_sale_orders_ids: List[str] = []
    linked_agents_ids: List[str] = []
    delivering_agent_id: Optional[str] = None
    isDelivered: bool = False
    matching_sale_orders: List[Dict[str, Any]] = []
    created: datetime = Field(default_factory=datetime.utcnow)
    lastUpdated: datetime = Field(default_factory=datetime.utcnow)