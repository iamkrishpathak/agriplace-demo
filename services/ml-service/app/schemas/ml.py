from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class DemandPredictRequest(BaseModel):
    crop_id: str
    region: str
    horizon_days: int

class DemandPredictResponse(BaseModel):
    crop_id: str
    region: str
    horizon_days: int
    demand_level: str
    confidence: float
    proxy_basis: str

class LocationCoords(BaseModel):
    location_id: str
    latitude: float
    longitude: float
    type: str # PICKUP or DROPOFF

class RouteOptimizeRequest(BaseModel):
    vehicle_id: str
    vehicle_capacity_kg: float
    start_location: LocationCoords
    stops: List[LocationCoords]

class RouteOptimizeResponse(BaseModel):
    vehicle_id: str
    total_distance_km: float
    stops_sequence: List[str]

class QualityPredictRequest(BaseModel):
    image_url: str
    crop_id: str

class QualityPredictResponse(BaseModel):
    predicted_grade: str
    confidence: float
    features_detected: List[str]
