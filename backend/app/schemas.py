from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field

from backend.app.models import Grade, RoleName


class ApiResponse(BaseModel):
    success: bool
    data: Any = None
    message: str | None = None
    error: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=6)
    role: RoleName | None = None


class RegisterRequest(BaseModel):
    name: str
    email: str
    phone: str | None = None
    password: str = Field(min_length=8)
    role: RoleName
    preferred_language: Literal["en", "hi"] = "en"


class ListingCreate(BaseModel):
    crop: str = "Tomato"
    quantity_kg: float = Field(gt=0)
    available_date: date
    grade: Grade
    expected_price_per_kg: float | None = Field(default=None, gt=0)
    pickup_location_id: str | None = None
    image_url: str | None = None


class SaleEstimateRequest(BaseModel):
    crop: str = "Tomato"
    quantity_kg: float = Field(gt=0)
    grade: Grade = Grade.A
    available_date: date
    pickup_location_id: str | None = None


class BuyerRequirementCreate(BaseModel):
    crop: str = "Tomato"
    required_quantity_kg: float = Field(gt=0)
    grade: Grade = Grade.A
    needed_by: date
    max_price_per_kg: float = Field(gt=0)
    destination_location_id: str | None = None
    recurring: bool = False


class RouteLocation(BaseModel):
    id: str | None = None
    label: str
    latitude: float
    longitude: float
    quantity_kg: float = 0
    stop_type: Literal["DEPOT", "PICKUP", "BUYER"] = "PICKUP"


class VehicleCapacity(BaseModel):
    id: str | None = None
    label: str = "Mini Truck"
    capacity_kg: int = Field(gt=0)


class RouteOptimizeRequest(BaseModel):
    depot: RouteLocation
    pickups: list[RouteLocation]
    buyer: RouteLocation
    vehicles: list[VehicleCapacity]
    cost_per_km: float = 24.0
    deadline_hours: float | None = None


class PickupConfirmRequest(BaseModel):
    stop_id: str
    actual_quantity_kg: float = Field(ge=0)
    grade: str = "Grade A"
    photo_url: str | None = None
    weighing_slip_url: str | None = None
    notes: str | None = None


class DeliveryConfirmRequest(BaseModel):
    delivered_quantity_kg: float = Field(ge=0)
    decision: Literal["Accepted", "Partially Accepted", "Rejected"] = "Accepted"
    digital_signature: str
    photo_url: str | None = None
    notes: str | None = None


class IncidentCreate(BaseModel):
    incident_type: Literal[
        "Vehicle Accident",
        "Vehicle Breakdown",
        "Road Closure",
        "Produce Damage",
        "Weather Event",
        "Buyer Unavailable",
        "Other",
    ]
    description: str
    latitude: float | None = None
    longitude: float | None = None
    evidence_urls: list[str] = Field(default_factory=list)


class QualityPredictRequest(BaseModel):
    crop: str = "Tomato"
    image_url: str | None = None
    declared_grade: Grade = Grade.A


class DemandPredictRequest(BaseModel):
    crop: str = "Tomato"
    region: str = "Nashik-Mumbai"
    horizon_days: int = Field(default=5, ge=1, le=30)


class MatchScoreRequest(BaseModel):
    requirement_id: str
    listing_id: str


class MatchingWeightsUpdate(BaseModel):
    quantity: float = Field(ge=0)
    quality: float = Field(ge=0)
    distance: float = Field(ge=0)
    price: float = Field(ge=0)
    availability: float = Field(ge=0)
    reliability: float = Field(ge=0)
