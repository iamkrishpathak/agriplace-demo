from pydantic import BaseModel, Field
from typing import Optional, List

class LocationCreate(BaseModel):
    label: str
    address: str
    district: str
    state: str
    latitude: float
    longitude: float
    location_type: str

class LocationResponse(LocationCreate):
    id: str
    user_id: Optional[str]
    data_classification: str

    class Config:
        from_attributes = True

class FarmerProfileCreate(BaseModel):
    village: str
    district: str
    state: str
    land_acres: float
    fpo_id: Optional[str] = None

class FarmerProfileResponse(FarmerProfileCreate):
    id: str
    user_id: str
    verification_status: str

    class Config:
        from_attributes = True

class BuyerProfileCreate(BaseModel):
    buyer_type: str
    business_name: str
    gstin: Optional[str] = None

class BuyerProfileResponse(BuyerProfileCreate):
    id: str
    user_id: str
    verification_status: str

    class Config:
        from_attributes = True

class TransporterProfileCreate(BaseModel):
    company_name: str
    license_number: str

class TransporterProfileResponse(TransporterProfileCreate):
    id: str
    user_id: str
    verification_status: str

    class Config:
        from_attributes = True

class VehicleCreate(BaseModel):
    registration_number: str
    vehicle_type: str
    capacity_kg: float
    cold_chain: bool = False

class VehicleResponse(VehicleCreate):
    id: str
    transporter_id: str
    document_status: str

    class Config:
        from_attributes = True
