from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from app.models.marketplace import Grade

class ListingCreate(BaseModel):
    crop: str
    quantity_kg: float
    available_date: date
    grade: Grade
    expected_price_per_kg: float
    image_url: Optional[str] = None
    pickup_location_id: str

class ListingResponse(BaseModel):
    id: str
    farmer_id: str
    crop_id: str
    quantity_kg: float
    available_date: date
    grade: str
    status: str
    expected_price_per_kg: float
    location_id: str
    image_url: Optional[str]

    class Config:
        from_attributes = True

class RequirementCreate(BaseModel):
    crop: str
    required_quantity_kg: float
    grade: Grade
    needed_by: date
    max_price_per_kg: float
    recurring: bool = False
    destination_location_id: str

class RequirementResponse(BaseModel):
    id: str
    buyer_id: str
    crop_id: str
    required_quantity_kg: float
    grade: str
    needed_by: date
    max_price_per_kg: float
    status: str
    destination_location_id: str

    class Config:
        from_attributes = True
