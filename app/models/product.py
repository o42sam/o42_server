from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class ProductCategory(str, Enum):
    phones_and_gadgets = "phones and gadgets"
    appliances = "appliances"
    clothing = "clothing"
    shoes_and_accessories = "shoes and accesories"
    cars = "cars"
    jewelry = "jewelry"
    pharmaceuticals = "pharmaceuticals"
    housing_and_real_estate = "housing and real estate"
    gift_items = "gift items"
    food_stuff = "food stuff"
    kiddies = "kiddies"
    books_and_stationery = "books and stationery"
    furniture_and_finishing = "furniture and finishing"
    pets = "pets"
    household_items = "household items"
    hardware = "hardware"

class ProductCondition(str, Enum):
    brand_new = "brand new"
    refurbished = "refurbished"
    faulty = "faulty"

class ProductBase(BaseModel):
    name: str
    description: str
    category: ProductCategory
    condition: ProductCondition
    images: List[str] = []
    video: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductInDB(ProductBase):
    id: str = Field(..., alias="_id")
    created: datetime = Field(default_factory=datetime.utcnow)
    lastUpdated: datetime = Field(default_factory=datetime.utcnow)