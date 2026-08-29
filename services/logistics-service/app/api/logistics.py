from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.security import get_current_user, CurrentUser, require_roles
from app.models.logistics import Delivery, DeliveryStop, DeliveryStatus, Incident
from app.schemas.logistics import DeliveryCreate, DeliveryResponse, IncidentCreate
import httpx
from app.core.config import settings

router = APIRouter()

def api_response(data=None, error=None, success=True):
    return {"success": success, "data": data, "error": error}

@router.post("/", response_model=dict)
def create_delivery(payload: DeliveryCreate, db: Session = Depends(get_db)):
    # In a real microservice, OrderService might call this without user context (internal API)
    delivery = Delivery(
        order_id=payload.order_id,
        cargo_kg=payload.cargo_kg,
        estimated_distance_km=payload.estimated_distance_km,
        estimated_duration_hours=payload.estimated_duration_hours,
        estimated_earnings=payload.estimated_earnings
    )
    db.add(delivery)
    db.flush()

    for s in payload.stops:
        stop = DeliveryStop(
            delivery_id=delivery.id,
            location_id=s.location_id,
            stop_type=s.stop_type,
            sequence=s.sequence,
            planned_quantity_kg=s.planned_quantity_kg
        )
        db.add(stop)

    db.commit()
    db.refresh(delivery)
    return api_response(DeliveryResponse.model_validate(delivery).model_dump())

@router.get("/jobs/available", response_model=dict)
def get_available_jobs(user: CurrentUser = Depends(require_roles(["TRANSPORTER"])), db: Session = Depends(get_db)):
    deliveries = db.query(Delivery).filter(Delivery.status == DeliveryStatus.REQUESTED).all()
    return api_response([DeliveryResponse.model_validate(d).model_dump() for d in deliveries])

@router.post("/jobs/{delivery_id}/accept", response_model=dict)
def accept_job(delivery_id: str, user: CurrentUser = Depends(require_roles(["TRANSPORTER"])), db: Session = Depends(get_db)):
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    if delivery.status != DeliveryStatus.REQUESTED:
        raise HTTPException(status_code=400, detail="Delivery not available")
    
    delivery.transporter_id = user.id
    delivery.status = DeliveryStatus.ACCEPTED
    db.commit()
    return api_response(DeliveryResponse.model_validate(delivery).model_dump())

@router.post("/jobs/{delivery_id}/incident", response_model=dict)
def report_incident(delivery_id: str, payload: IncidentCreate, user: CurrentUser = Depends(require_roles(["TRANSPORTER"])), db: Session = Depends(get_db)):
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    
    incident = Incident(
        delivery_id=delivery.id,
        reported_by_id=user.id,
        incident_type=payload.incident_type,
        description=payload.description,
        latitude=payload.latitude,
        longitude=payload.longitude,
        evidence_urls=payload.evidence_urls
    )
    delivery.status = DeliveryStatus.INCIDENT_REPORTED
    db.add(incident)
    db.commit()
    return api_response({"incident_id": incident.id, "status": incident.status})
