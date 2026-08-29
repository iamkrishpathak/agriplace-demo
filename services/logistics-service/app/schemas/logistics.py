from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class StopCreate(BaseModel):
    location_id: str
    stop_type: str
    sequence: int
    planned_quantity_kg: float

class DeliveryCreate(BaseModel):
    order_id: str
    cargo_kg: float
    estimated_distance_km: float = 0.0
    estimated_duration_hours: float = 0.0
    estimated_earnings: float = 0.0
    stops: List[StopCreate]

class DeliveryResponse(BaseModel):
    id: str
    order_id: str
    transporter_id: Optional[str]
    status: str
    cargo_kg: float

    class Config:
        from_attributes = True

class IncidentCreate(BaseModel):
    incident_type: str
    description: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    evidence_urls: List[str] = []
