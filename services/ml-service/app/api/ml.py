from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.ml import DemandPrediction, RoutePlan
from app.schemas.ml import DemandPredictRequest, DemandPredictResponse, RouteOptimizeRequest, RouteOptimizeResponse, QualityPredictRequest, QualityPredictResponse
from app.inference.models import DemandModel, RoutingModel

router = APIRouter()
demand_model = DemandModel()
routing_model = RoutingModel()

def api_response(data=None, error=None, success=True):
    return {"success": success, "data": data, "error": error}

@router.post("/demand/predict", response_model=dict)
def predict_demand(payload: DemandPredictRequest, db: Session = Depends(get_db)):
    res = demand_model.predict(payload.crop_id, payload.region, payload.horizon_days)
    
    pred = DemandPrediction(
        crop_id=payload.crop_id,
        region=payload.region,
        horizon_days=payload.horizon_days,
        demand_level=res["level"],
        confidence=res["confidence"],
        proxy_basis="RandomForest Inference"
    )
    db.add(pred)
    db.commit()
    
    return api_response(DemandPredictResponse(
        crop_id=payload.crop_id,
        region=payload.region,
        horizon_days=payload.horizon_days,
        demand_level=pred.demand_level,
        confidence=pred.confidence,
        proxy_basis=pred.proxy_basis
    ).model_dump())

@router.post("/routing/optimize", response_model=dict)
def optimize_route(payload: RouteOptimizeRequest, db: Session = Depends(get_db)):
    if not payload.stops:
        raise HTTPException(status_code=400, detail="No stops provided")
        
    res = routing_model.optimize(payload.start_location, payload.stops, payload.vehicle_capacity_kg)
    
    plan = RoutePlan(
        vehicle_id=payload.vehicle_id,
        total_distance_km=res["distance_km"],
        stops_sequence=res["route"]
    )
    db.add(plan)
    db.commit()
    
    return api_response(RouteOptimizeResponse(
        vehicle_id=payload.vehicle_id,
        total_distance_km=plan.total_distance_km,
        stops_sequence=plan.stops_sequence
    ).model_dump())

@router.post("/quality/predict", response_model=dict)
def predict_quality(payload: QualityPredictRequest):
    # Dummy CV implementation for SIH prototype
    return api_response(QualityPredictResponse(
        predicted_grade="Grade A",
        confidence=0.89,
        features_detected=["uniform_color", "no_blemishes", "optimal_size"]
    ).model_dump())
