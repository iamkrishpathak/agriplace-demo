from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.order import OrderStatus

class OrderItemCreate(BaseModel):
    listing_id: str
    quantity_kg: float

class OrderCreate(BaseModel):
    requirement_id: Optional[str] = None
    items: List[OrderItemCreate]

class OrderItemResponse(BaseModel):
    id: str
    order_id: str
    listing_id: str
    seller_id: str
    crop_id: str
    quantity_kg: float
    price_per_kg: float
    quality_status: str

    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: str
    order_number: str
    buyer_id: str
    requirement_id: Optional[str]
    status: str
    total_quantity_kg: float
    total_value: float
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True
