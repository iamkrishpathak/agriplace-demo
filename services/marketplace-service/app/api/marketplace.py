from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.security import get_current_user, CurrentUser, require_roles
from app.models.marketplace import Crop, ProduceListing, BuyerRequirement, ListingStatus, OrderMatch
from app.schemas.marketplace import ListingCreate, ListingResponse, RequirementCreate, RequirementResponse
import httpx
from app.core.config import settings

router = APIRouter()

def api_response(data=None, error=None, success=True):
    return {"success": success, "data": data, "error": error}

def get_or_create_crop(db: Session, crop_name: str) -> Crop:
    crop = db.query(Crop).filter(Crop.name.ilike(crop_name)).first()
    if not crop:
        crop = Crop(name=crop_name.title(), hindi_name=crop_name.title())
        db.add(crop)
        db.flush()
    return crop

@router.post("/listings", response_model=dict)
def create_listing(payload: ListingCreate, user: CurrentUser = Depends(require_roles(["FARMER"])), db: Session = Depends(get_db)):
    crop = get_or_create_crop(db, payload.crop)
    
    # We could optionally verify location_id via User Service here
    
    listing = ProduceListing(
        farmer_id=user.id,
        crop_id=crop.id,
        location_id=payload.pickup_location_id,
        quantity_kg=payload.quantity_kg,
        available_date=payload.available_date,
        grade=payload.grade,
        expected_price_per_kg=payload.expected_price_per_kg,
        image_url=payload.image_url
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return api_response(ListingResponse.model_validate(listing).model_dump())

@router.get("/listings", response_model=dict)
def get_listings(db: Session = Depends(get_db)):
    listings = db.query(ProduceListing).filter(ProduceListing.status == ListingStatus.ACTIVE).all()
    return api_response([ListingResponse.model_validate(l).model_dump() for l in listings])

@router.post("/requirements", response_model=dict)
def create_requirement(payload: RequirementCreate, user: CurrentUser = Depends(require_roles(["BUYER"])), db: Session = Depends(get_db)):
    crop = get_or_create_crop(db, payload.crop)
    req = BuyerRequirement(
        buyer_id=user.id,
        crop_id=crop.id,
        destination_location_id=payload.destination_location_id,
        required_quantity_kg=payload.required_quantity_kg,
        grade=payload.grade,
        needed_by=payload.needed_by,
        max_price_per_kg=payload.max_price_per_kg,
        recurring=payload.recurring
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return api_response(RequirementResponse.model_validate(req).model_dump())

@router.get("/requirements", response_model=dict)
def get_requirements(user: CurrentUser = Depends(require_roles(["BUYER"])), db: Session = Depends(get_db)):
    reqs = db.query(BuyerRequirement).filter(BuyerRequirement.buyer_id == user.id).all()
    return api_response([RequirementResponse.model_validate(r).model_dump() for r in reqs])

# Internal endpoint for Order Service to fetch listing details
@router.get("/internal/listings/{listing_id}", response_model=dict)
def get_listing_internal(listing_id: str, db: Session = Depends(get_db)):
    listing = db.query(ProduceListing).filter(ProduceListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return api_response(ListingResponse.model_validate(listing).model_dump())

@router.get("/internal/requirements/{requirement_id}", response_model=dict)
def get_requirement_internal(requirement_id: str, db: Session = Depends(get_db)):
    req = db.query(BuyerRequirement).filter(BuyerRequirement.id == requirement_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return api_response(RequirementResponse.model_validate(req).model_dump())
