from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.security import get_current_user, CurrentUser, require_roles
from app.models.profile import FarmerProfile, BuyerProfile, TransporterProfile, Vehicle, Location
from app.schemas.profile import (
    FarmerProfileCreate, FarmerProfileResponse,
    BuyerProfileCreate, BuyerProfileResponse,
    TransporterProfileCreate, TransporterProfileResponse,
    LocationCreate, LocationResponse,
    VehicleCreate, VehicleResponse
)

router = APIRouter()

def api_response(data=None, error=None, success=True):
    return {"success": success, "data": data, "error": error}

@router.post("/farmer", response_model=dict)
def create_farmer_profile(payload: FarmerProfileCreate, user: CurrentUser = Depends(require_roles(["FARMER"])), db: Session = Depends(get_db)):
    existing = db.query(FarmerProfile).filter(FarmerProfile.user_id == user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Profile already exists")
    
    profile = FarmerProfile(user_id=user.id, **payload.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return api_response(FarmerProfileResponse.model_validate(profile).model_dump())

@router.get("/farmer/me", response_model=dict)
def get_farmer_profile(user: CurrentUser = Depends(require_roles(["FARMER"])), db: Session = Depends(get_db)):
    profile = db.query(FarmerProfile).filter(FarmerProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return api_response(FarmerProfileResponse.model_validate(profile).model_dump())

@router.post("/buyer", response_model=dict)
def create_buyer_profile(payload: BuyerProfileCreate, user: CurrentUser = Depends(require_roles(["BUYER"])), db: Session = Depends(get_db)):
    existing = db.query(BuyerProfile).filter(BuyerProfile.user_id == user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Profile already exists")
    
    profile = BuyerProfile(user_id=user.id, **payload.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return api_response(BuyerProfileResponse.model_validate(profile).model_dump())

@router.get("/buyer/me", response_model=dict)
def get_buyer_profile(user: CurrentUser = Depends(require_roles(["BUYER"])), db: Session = Depends(get_db)):
    profile = db.query(BuyerProfile).filter(BuyerProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return api_response(BuyerProfileResponse.model_validate(profile).model_dump())

@router.post("/transporter", response_model=dict)
def create_transporter_profile(payload: TransporterProfileCreate, user: CurrentUser = Depends(require_roles(["TRANSPORTER"])), db: Session = Depends(get_db)):
    existing = db.query(TransporterProfile).filter(TransporterProfile.user_id == user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Profile already exists")
    
    profile = TransporterProfile(user_id=user.id, **payload.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return api_response(TransporterProfileResponse.model_validate(profile).model_dump())

@router.get("/transporter/me", response_model=dict)
def get_transporter_profile(user: CurrentUser = Depends(require_roles(["TRANSPORTER"])), db: Session = Depends(get_db)):
    profile = db.query(TransporterProfile).filter(TransporterProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    vehicles = db.query(Vehicle).filter(Vehicle.transporter_id == profile.id).all()
    resp = TransporterProfileResponse.model_validate(profile).model_dump()
    resp["vehicles"] = [VehicleResponse.model_validate(v).model_dump() for v in vehicles]
    return api_response(resp)

@router.post("/transporter/vehicles", response_model=dict)
def add_vehicle(payload: VehicleCreate, user: CurrentUser = Depends(require_roles(["TRANSPORTER"])), db: Session = Depends(get_db)):
    profile = db.query(TransporterProfile).filter(TransporterProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Transporter profile not found")
    
    vehicle = Vehicle(transporter_id=profile.id, **payload.model_dump())
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return api_response(VehicleResponse.model_validate(vehicle).model_dump())

@router.post("/locations", response_model=dict)
def add_location(payload: LocationCreate, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    loc = Location(user_id=user.id, **payload.model_dump())
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return api_response(LocationResponse.model_validate(loc).model_dump())

@router.get("/locations", response_model=dict)
def get_locations(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    locs = db.query(Location).filter(Location.user_id == user.id).all()
    return api_response([LocationResponse.model_validate(l).model_dump() for l in locs])

# Internal API for other services to get user info/locations
@router.get("/internal/users/{user_id}/profile", response_model=dict)
def get_user_profile_internal(user_id: str, db: Session = Depends(get_db)):
    f = db.query(FarmerProfile).filter(FarmerProfile.user_id == user_id).first()
    if f:
        return api_response({"role": "FARMER", "profile": FarmerProfileResponse.model_validate(f).model_dump()})
    b = db.query(BuyerProfile).filter(BuyerProfile.user_id == user_id).first()
    if b:
        return api_response({"role": "BUYER", "profile": BuyerProfileResponse.model_validate(b).model_dump()})
    t = db.query(TransporterProfile).filter(TransporterProfile.user_id == user_id).first()
    if t:
        return api_response({"role": "TRANSPORTER", "profile": TransporterProfileResponse.model_validate(t).model_dump()})
    
    raise HTTPException(status_code=404, detail="Profile not found")

@router.get("/internal/locations/{location_id}", response_model=dict)
def get_location_internal(location_id: str, db: Session = Depends(get_db)):
    loc = db.query(Location).filter(Location.id == location_id).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    return api_response(LocationResponse.model_validate(loc).model_dump())
