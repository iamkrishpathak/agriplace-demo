from datetime import date, timedelta
from statistics import mean

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.app.models import (
    Alert,
    BuyerRequirement,
    Crop,
    DemandPrediction,
    Grade,
    MarketArrival,
    MarketPrice,
    PricePrediction,
    RequirementStatus,
)


GRADE_MULTIPLIER = {
    Grade.A: 1.04,
    Grade.B: 1.0,
    Grade.C: 0.9,
}


def get_crop_by_name(db: Session, crop_name: str) -> Crop:
    crop = db.scalar(select(Crop).where(Crop.name.ilike(crop_name)))
    if crop:
        return crop
    crop = Crop(name=crop_name.title(), hindi_name=crop_name.title(), perishability="MEDIUM")
    db.add(crop)
    db.flush()
    return crop


def latest_market_prices(db: Session, crop: Crop) -> list[MarketPrice]:
    return list(
        db.scalars(
            select(MarketPrice)
            .where(MarketPrice.crop_id == crop.id)
            .order_by(desc(MarketPrice.arrival_date), MarketPrice.market)
            .limit(8)
        )
    )


def sale_estimate(
    db: Session,
    *,
    crop_name: str,
    quantity_kg: float,
    grade: Grade,
    available_date: date,
) -> dict:
    crop = get_crop_by_name(db, crop_name)
    prices = latest_market_prices(db, crop)

    if prices:
        min_per_kg = mean([p.min_price for p in prices]) / 100
        max_per_kg = mean([p.max_price for p in prices]) / 100
        modal_per_kg = mean([p.modal_price for p in prices]) / 100
        source_label = "Sample mandi feed shaped from data.gov.in/Agmarknet schema"
    else:
        min_per_kg, max_per_kg, modal_per_kg = 22, 28, 25
        source_label = "Fallback demo baseline"

    recommended = round(modal_per_kg * GRADE_MULTIPLIER[grade], 2)
    gross = round(recommended * quantity_kg, 2)
    logistics_per_kg = 1.45 if crop.perishability == "HIGH" else 1.1
    logistics = round(quantity_kg * logistics_per_kg, 2)
    platform_fee = round(gross * 0.01, 2)
    quality_handling = round(quantity_kg * 0.35, 2)
    net = round(gross - logistics - platform_fee - quality_handling, 2)

    demand_qty = db.scalar(
        select(BuyerRequirement.required_quantity_kg)
        .where(BuyerRequirement.crop_id == crop.id, BuyerRequirement.status == RequirementStatus.OPEN)
        .order_by(desc(BuyerRequirement.created_at))
        .limit(1)
    )
    demand_indicator = "HIGH" if (demand_qty or 0) >= quantity_kg else "MEDIUM"

    arrival_rows = list(
        db.scalars(
            select(MarketArrival)
            .where(
                MarketArrival.crop_id == crop.id,
                MarketArrival.arrival_date >= date.today() - timedelta(days=7),
            )
            .limit(12)
        )
    )
    arrival_proxy = mean([row.arrival_quantity_tonnes for row in arrival_rows]) if arrival_rows else 0
    glut_risk = "LOW"
    if arrival_proxy > 900 and demand_indicator != "HIGH":
        glut_risk = "MEDIUM"
    if arrival_proxy > 1200:
        glut_risk = "HIGH"

    return {
        "label": "AI estimate - indicative, not guaranteed",
        "crop": crop.name,
        "quantity_kg": quantity_kg,
        "grade": grade.value,
        "available_date": available_date.isoformat(),
        "market_range_per_kg": {
            "min": round(min_per_kg, 2),
            "max": round(max_per_kg, 2),
            "unit": "INR/kg",
        },
        "recommended_listing_price_per_kg": recommended,
        "expected_gross": gross,
        "transparent_breakdown": {
            "buyer_pays_per_kg": recommended,
            "farmer_receives_per_kg_estimate": round(net / quantity_kg, 2),
            "transport_per_kg": logistics_per_kg,
            "platform_service_fee": platform_fee,
            "quality_handling": quality_handling,
        },
        "estimated_logistics": logistics,
        "estimated_net": net,
        "potential_buyer_demand": demand_indicator,
        "arrival_proxy_tonnes": round(arrival_proxy, 2),
        "possible_glut_risk": glut_risk,
        "source_note": source_label,
        "data_classification": {
            "market_prices": "SOURCE_READY/SYNTHETIC_SAMPLE",
            "forecast": "DERIVED",
            "buyer_demand": "SYNTHETIC",
            "arrival_signal": "PROXY",
        },
    }


def price_prediction(db: Session, crop_name: str, horizon_days: int = 7) -> dict:
    crop = get_crop_by_name(db, crop_name)
    estimate = sale_estimate(
        db,
        crop_name=crop.name,
        quantity_kg=1000,
        grade=Grade.A,
        available_date=date.today() + timedelta(days=horizon_days),
    )
    base_min = estimate["market_range_per_kg"]["min"]
    base_max = estimate["market_range_per_kg"]["max"]
    volatility = min(0.16, 0.04 + horizon_days * 0.006)
    pred = PricePrediction(
        crop_id=crop.id,
        market="Nashik-Mumbai corridor",
        horizon_days=horizon_days,
        predicted_min_price=round(base_min * (1 - volatility), 2),
        predicted_max_price=round(base_max * (1 + volatility), 2),
        confidence=max(0.54, round(0.82 - horizon_days * 0.01, 2)),
        model_name="baseline-xgboost-ready-demo",
    )
    db.add(pred)
    db.flush()
    return {
        "prediction_id": pred.id,
        "crop": crop.name,
        "market": pred.market,
        "horizon_days": horizon_days,
        "predicted_range_per_kg": {
            "min": pred.predicted_min_price,
            "max": pred.predicted_max_price,
            "unit": "INR/kg",
        },
        "confidence": pred.confidence,
        "model": pred.model_name,
        "research_path": "PREPARE-inspired baseline first; CNN/GNN later with sufficient data.",
        "disclaimer": "Forecast is indicative and should not be treated as a guaranteed price.",
    }


def demand_prediction(db: Session, crop_name: str, region: str, horizon_days: int) -> dict:
    crop = get_crop_by_name(db, crop_name)
    open_requirements = db.scalars(
        select(BuyerRequirement).where(
            BuyerRequirement.crop_id == crop.id,
            BuyerRequirement.status == RequirementStatus.OPEN,
        )
    ).all()
    qty = sum(req.required_quantity_kg for req in open_requirements)
    level = "LOW"
    if qty > 1000:
        level = "MEDIUM"
    if qty > 1800:
        level = "HIGH"
    pred = DemandPrediction(
        crop_id=crop.id,
        region=region,
        horizon_days=horizon_days,
        demand_level=level,
        proxy_basis="Active buyer requirements plus market-arrival proxy",
        confidence=0.74,
    )
    db.add(pred)
    db.flush()
    return {
        "prediction_id": pred.id,
        "crop": crop.name,
        "region": region,
        "horizon_days": horizon_days,
        "demand_level": level,
        "open_requirement_kg": round(qty, 2),
        "proxy_basis": pred.proxy_basis,
        "confidence": pred.confidence,
        "disclaimer": "Market arrivals are a proxy signal and are not the same as true consumer demand.",
    }


def active_alerts_for_user(db: Session, user_id: str | None) -> list[dict]:
    alerts = db.scalars(
        select(Alert).where((Alert.user_id == user_id) | (Alert.user_id.is_(None))).order_by(desc(Alert.created_at))
    ).all()
    return [
        {
            "id": alert.id,
            "type": alert.alert_type,
            "severity": alert.severity,
            "title": alert.title,
            "message": alert.message,
            "data_classification": alert.data_classification.value,
        }
        for alert in alerts
    ]

