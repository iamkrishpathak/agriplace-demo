from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import (
    BuyerRequirement,
    Grade,
    ListingStatus,
    OrderMatch,
    ProduceListing,
    ReputationScore,
    RoleName,
)
from backend.app.services.geo import derived_road_km


MATCHING_WEIGHTS: dict[str, float] = {
    "quantity": 0.30,
    "quality": 0.20,
    "distance": 0.15,
    "price": 0.15,
    "availability": 0.10,
    "reliability": 0.10,
}

GRADE_RANK = {Grade.A: 3, Grade.B: 2, Grade.C: 1}


def _quality_score(listing_grade: Grade, required_grade: Grade) -> float:
    if GRADE_RANK[listing_grade] >= GRADE_RANK[required_grade]:
        return 1.0
    return max(0.35, GRADE_RANK[listing_grade] / GRADE_RANK[required_grade])


def _availability_score(available: date, needed_by: date) -> float:
    if available <= needed_by:
        return 1.0
    delay = (available - needed_by).days
    return max(0.0, 1 - delay * 0.25)


def _distance_score(distance_km: float) -> float:
    if distance_km <= 60:
        return 1.0
    if distance_km >= 300:
        return 0.2
    return round(1 - ((distance_km - 60) / 300), 3)


def _price_score(listing_price: float, max_price: float) -> float:
    if listing_price <= max_price:
        return 1.0
    overage = (listing_price - max_price) / max_price
    return max(0.0, 1 - overage * 3)


def reliability_for_user(db: Session, user_id: str) -> float:
    reputation = db.scalar(
        select(ReputationScore).where(
            ReputationScore.user_id == user_id,
            ReputationScore.role == RoleName.FARMER,
        )
    )
    return (reputation.score / 100) if reputation else 0.78


def score_listing(db: Session, requirement: BuyerRequirement, listing: ProduceListing) -> dict[str, Any]:
    distance_km = derived_road_km(
        listing.location.latitude,
        listing.location.longitude,
        requirement.destination.latitude,
        requirement.destination.longitude,
    )
    scores = {
        "quantity": min(1.0, listing.quantity_kg / requirement.required_quantity_kg),
        "quality": _quality_score(listing.grade, requirement.grade),
        "distance": _distance_score(distance_km),
        "price": _price_score(listing.expected_price_per_kg, requirement.max_price_per_kg),
        "availability": _availability_score(listing.available_date, requirement.needed_by),
        "reliability": reliability_for_user(db, listing.farmer_id),
    }
    weighted = sum(scores[key] * MATCHING_WEIGHTS[key] for key in MATCHING_WEIGHTS)
    return {
        "score": round(weighted * 100, 2),
        "breakdown": {key: round(value * 100, 1) for key, value in scores.items()},
        "distance_km": distance_km,
    }


def find_matches(db: Session, requirement: BuyerRequirement, persist: bool = False) -> dict[str, Any]:
    listings = db.scalars(
        select(ProduceListing)
        .where(
            ProduceListing.crop_id == requirement.crop_id,
            ProduceListing.status == ListingStatus.ACTIVE,
            ProduceListing.quantity_kg > 0,
        )
        .order_by(ProduceListing.available_date)
    ).all()
    scored = []
    for listing in listings:
        details = score_listing(db, requirement, listing)
        if details["score"] >= 45:
            scored.append((listing, details))
    scored.sort(key=lambda item: item[1]["score"], reverse=True)

    remaining = requirement.required_quantity_kg
    selected = []
    for listing, details in scored:
        if remaining <= 0:
            break
        qty = min(remaining, listing.quantity_kg)
        remaining -= qty
        payload = {
            "listing_id": listing.id,
            "seller_id": listing.farmer_id,
            "seller_name": listing.farmer.name,
            "crop": listing.crop.name,
            "quantity_kg": qty,
            "available_quantity_kg": listing.quantity_kg,
            "grade": listing.grade.value,
            "price_per_kg": listing.expected_price_per_kg,
            "location": {
                "id": listing.location.id,
                "label": listing.location.label,
                "district": listing.location.district,
                "state": listing.location.state,
                "latitude": listing.location.latitude,
                "longitude": listing.location.longitude,
            },
            "score": details["score"],
            "score_breakdown": details["breakdown"],
            "distance_km": details["distance_km"],
        }
        selected.append(payload)
        if persist:
            db.add(
                OrderMatch(
                    requirement_id=requirement.id,
                    listing_id=listing.id,
                    quantity_kg=qty,
                    score=details["score"],
                    score_breakdown=details["breakdown"],
                )
            )

    total_matched = sum(item["quantity_kg"] for item in selected)
    return {
        "requirement_id": requirement.id,
        "required_quantity_kg": requirement.required_quantity_kg,
        "matched_quantity_kg": total_matched,
        "shortfall_kg": max(0, requirement.required_quantity_kg - total_matched),
        "is_fully_matched": total_matched >= requirement.required_quantity_kg,
        "average_quality": requirement.grade.value if selected else None,
        "matches": selected,
        "weights": MATCHING_WEIGHTS,
        "method": "configurable weighted scoring, not blind ML",
    }

