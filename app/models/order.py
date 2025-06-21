from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime
from enum import Enum

class SaleType(str, Enum):
    fixed_price = "fixed-price"
    auction = "auction"
    negotiation = "negotiation"

# Sale Order
class SaleOrderBase(BaseModel):
    creator_id: str
    product_id: str
    sale_type: SaleType
    price: float # For fixed-price, this is the price. For others, it's the starting price.
    commission_percentage: float = Field(..., ge=0, le=100)
    location: Any # GeoJSON Point

class SaleOrderCreate(SaleOrderBase):
    pass

class SaleOrderInDB(SaleOrderBase):
    id: str = Field(..., alias="_id")
    linked_agents_ids: List[str] = []
    delivering_agent_id: Optional[str] = None
    isDelivered: bool = False
    created: datetime = Field(default_factory=datetime.utcnow)
    lastUpdated: datetime = Field(default_factory=datetime.utcnow)

# Purchase Order
class PurchaseOrderBase(BaseModel):
    creator_id: str
    product_description: str
    product_image: str # URL to the generated image

class PurchaseOrderCreate(PurchaseOrderBase):
    pass

class PurchaseOrderInDB(PurchaseOrderBase):
    id: str = Field(..., alias="_id")
    matching_sale_orders_ids: List[str] = []
    linked_agents_ids: List[str] = []
    delivering_agent_id: Optional[str] = None
    isDelivered: bool = False
    created: datetime = Field(default_factory=datetime.utcnow)
    lastUpdated: datetime = Field(default_factory=datetime.utcnow)