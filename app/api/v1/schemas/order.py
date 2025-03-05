from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class Product(BaseModel):
    category: str
    price: float
    quantity: int
    description: str
    photos: List[str]
    videos: List[str]

class OrderBase(BaseModel):
    type: str  # "sale" or "purchase"
    product: Product
    order_description: str
    order_time: datetime
    order_location: List[float]  # [lon, lat]

class OrderCreate(OrderBase):
    commission: Optional[float]  # Only for sale

class OrderUpdate(BaseModel):
    product: Optional[Product]
    order_description: Optional[str]
    order_location: Optional[List[float]]
    commission: Optional[float]

class Order(OrderBase):
    id: str
    seller_id: Optional[str]
    buyer_id: Optional[str]
    commission: Optional[float]
    matching_orders: List[str] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        arbitrary_types_allowed = True