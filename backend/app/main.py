from datetime import date, timedelta
from typing import Any, Callable

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from backend.app.database import SessionLocal, get_db, init_db
from backend.app.models import (
    Alert,
    BuyerProfile,
    BuyerRequirement,
    DataSource,
    Delivery,
    DeliveryRecord,
    DeliveryStatus,
    DeliveryStop,
    Dispute,
    FarmerProfile,
    Grade,
    Incident,
    ListingStatus,
    MarketPrice,
    Notification,
    Order,
    OrderItem,
    OrderStatus,
    Payment,
    PaymentRelease,
    PaymentStatus,
    PickupRecord,
    ProduceListing,
    ReputationScore,
    RequirementStatus,
    Role,
    RoleName,
    RouteEvent,
    RoutePlan,
    StateRule,
    StopStatus,
    TransporterProfile,
    User,
    Vehicle,
)
from backend.app.schemas import (
    BuyerRequirementCreate,
    DeliveryConfirmRequest,
    DemandPredictRequest,
    IncidentCreate,
    ListingCreate,
    LoginRequest,
    MatchScoreRequest,
    MatchingWeightsUpdate,
    PickupConfirmRequest,
    QualityPredictRequest,
    RegisterRequest,
    RouteLocation,
    RouteOptimizeRequest,
    SaleEstimateRequest,
    VehicleCapacity,
)
from backend.app.seed import DEMO_PASSWORD, seed_db
from backend.app.services.audit import audit
from backend.app.services.market_intelligence import (
    active_alerts_for_user,
    demand_prediction,
    get_crop_by_name,
    price_prediction,
    sale_estimate,
)
from backend.app.services.matching import MATCHING_WEIGHTS, find_matches, score_listing
from backend.app.services.routing import optimize_cvrp
from backend.app.services.workflows import (
    create_delivery_for_order,
    create_protected_order_from_requirement,
    create_route_for_order,
    default_depot,
    demo_vehicle_capacities,
    order_pickup_locations,
)


app = FastAPI(
    title="AgriPlace API",
    version="0.1.0",
    description="Farmer-first agricultural marketplace prototype for SIH 2026.",
)
security = HTTPBearer(auto_error=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def api_response(data: Any = None, message: str | None = None, error: str | None = None, success: bool = True):
    return {"success": success, "data": data, "message": message, "error": error}


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=api_response(success=False, error=str(exc.detail), data=None),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=api_response(success=False, error="Validation failed", data={"details": exc.errors()}),
    )


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    db = SessionLocal()
    try:
        seed_db(db)
    finally:
        db.close()


def roles_for_user(user: User) -> list[str]:
    return [role.name.value for role in user.roles]


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token")
    user_id = payload.get("sub")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_roles(*allowed: RoleName) -> Callable:
    def _dependency(user: User = Depends(get_current_user)) -> User:
        actual = set(roles_for_user(user))
        expected = {role.value for role in allowed}
        if not actual.intersection(expected):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role not permitted for this API")
        return user

    return _dependency


def serialize_location(location) -> dict[str, Any]:
    return {
        "id": location.id,
        "label": location.label,
        "address": location.address,
        "district": location.district,
        "state": location.state,
        "latitude": location.latitude,
        "longitude": location.longitude,
        "type": location.location_type,
        "data_classification": location.data_classification.value,
    }


def serialize_listing(listing: ProduceListing) -> dict[str, Any]:
    return {
        "id": listing.id,
        "farmer": {"id": listing.farmer.id, "name": listing.farmer.name, "verified": listing.farmer.status.value},
        "crop": {"id": listing.crop.id, "name": listing.crop.name, "hindi_name": listing.crop.hindi_name},
        "quantity_kg": listing.quantity_kg,
        "available_date": listing.available_date.isoformat(),
        "grade": listing.grade.value,
        "status": listing.status.value,
        "expected_price_per_kg": listing.expected_price_per_kg,
        "location": serialize_location(listing.location),
        "image_url": listing.image_url,
        "perishable_controls": {
            "max_transit_hours": listing.max_transit_hours,
            "storage_requirement": listing.storage_requirement,
            "temperature_requirement": listing.temperature_requirement,
        },
        "data_classification": listing.data_classification.value,
    }


def serialize_requirement(requirement: BuyerRequirement) -> dict[str, Any]:
    return {
        "id": requirement.id,
        "buyer": {"id": requirement.buyer.id, "name": requirement.buyer.name},
        "crop": {"id": requirement.crop.id, "name": requirement.crop.name},
        "required_quantity_kg": requirement.required_quantity_kg,
        "grade": requirement.grade.value,
        "needed_by": requirement.needed_by.isoformat(),
        "max_price_per_kg": requirement.max_price_per_kg,
        "destination": serialize_location(requirement.destination),
        "status": requirement.status.value,
        "recurring": requirement.recurring,
    }


def serialize_payment(payment: Payment | None) -> dict[str, Any] | None:
    if not payment:
        return None
    return {
        "id": payment.id,
        "status": payment.status.value,
        "amount": payment.amount,
        "paid_amount": payment.paid_amount,
        "held_amount": payment.held_amount,
        "released_amount": payment.released_amount,
        "remaining_amount": payment.remaining_amount,
        "label": payment.label,
    }


def serialize_order(order: Order, db: Session | None = None) -> dict[str, Any]:
    payment = None
    if db:
        payment = db.scalar(select(Payment).where(Payment.order_id == order.id))
    return {
        "id": order.id,
        "order_number": order.order_number,
        "buyer": {"id": order.buyer.id, "name": order.buyer.name},
        "status": order.status.value,
        "payment_status": order.payment_status.value,
        "total_quantity_kg": order.total_quantity_kg,
        "total_value": order.total_value,
        "items": [
            {
                "id": item.id,
                "seller": {"id": item.seller.id, "name": item.seller.name},
                "crop": item.crop.name,
                "quantity_kg": item.quantity_kg,
                "price_per_kg": item.price_per_kg,
                "quality_status": item.quality_status,
                "location": serialize_location(item.listing.location),
            }
            for item in order.items
        ],
        "payment": serialize_payment(payment),
        "created_at": order.created_at.isoformat(),
        "data_classification": order.data_classification.value,
    }


def serialize_delivery(delivery: Delivery) -> dict[str, Any]:
    return {
        "id": delivery.id,
        "order_id": delivery.order_id,
        "order_number": delivery.order.order_number,
        "status": delivery.status.value,
        "transporter_id": delivery.transporter_id,
        "vehicle_id": delivery.vehicle_id,
        "cargo_kg": delivery.cargo_kg,
        "estimated_distance_km": delivery.estimated_distance_km,
        "estimated_duration_hours": delivery.estimated_duration_hours,
        "estimated_earnings": delivery.estimated_earnings,
        "route": delivery.route.route_payload if delivery.route else None,
        "stops": [
            {
                "id": stop.id,
                "type": stop.stop_type,
                "sequence": stop.sequence,
                "planned_quantity_kg": stop.planned_quantity_kg,
                "actual_quantity_kg": stop.actual_quantity_kg,
                "status": stop.status.value,
                "location": serialize_location(stop.location),
                "listing_id": stop.listing_id,
            }
            for stop in delivery.stops
        ],
    }


@app.get("/health")
def health() -> dict:
    return api_response(
        {
            "app": settings.app_name,
            "environment": settings.environment,
            "database": "connected",
            "routing_provider": settings.routing_provider,
        }
    )


@app.post("/auth/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> dict:
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        preferred_language=payload.preferred_language,
    )
    db.add(user)
    db.flush()
    db.add(Role(user_id=user.id, name=payload.role))
    audit(
        db,
        actor_id=user.id,
        action="auth.register",
        entity_type="User",
        entity_id=user.id,
        new_value={"email": user.email, "role": payload.role.value},
    )
    db.commit()
    return api_response({"id": user.id, "roles": [payload.role.value]}, "User registered")


@app.post("/auth/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> dict:
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    roles = roles_for_user(user)
    if payload.role and payload.role.value not in roles:
        raise HTTPException(status_code=403, detail="Requested role is not assigned to this user")
    token = create_access_token(user.id, roles)
    return api_response(
        {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "roles": roles,
                "preferred_language": user.preferred_language,
            },
        },
        "Login successful",
    )


@app.get("/auth/me")
def me(user: User = Depends(get_current_user)) -> dict:
    return api_response(
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "roles": roles_for_user(user),
            "preferred_language": user.preferred_language,
            "status": user.status.value,
        }
    )


@app.get("/demo/accounts")
def demo_accounts() -> dict:
    return api_response(
        {
            "password": DEMO_PASSWORD,
            "accounts": [
                {"role": "FARMER", "email": "farmer@agriplace.demo"},
                {"role": "BUYER", "email": "buyer@agriplace.demo"},
                {"role": "TRANSPORTER", "email": "transporter@agriplace.demo"},
                {"role": "ADMIN", "email": "admin@agriplace.demo"},
            ],
        }
    )


@app.get("/demo/scenario")
def demo_scenario(db: Session = Depends(get_db)) -> dict:
    order = db.scalar(select(Order).order_by(Order.created_at.desc()))
    delivery = db.scalar(select(Delivery).where(Delivery.order_id == order.id)) if order else None
    requirement = db.get(BuyerRequirement, order.requirement_id) if order and order.requirement_id else None
    return api_response(
        {
            "problem_statement": "Multiple intermediaries reduce farmer earnings and increase consumer prices.",
            "positioning": "Farmer-first direct marketplace with price intelligence, trusted payment protection, and pooled logistics.",
            "requirement": serialize_requirement(requirement) if requirement else None,
            "order": serialize_order(order, db) if order else None,
            "delivery": serialize_delivery(delivery) if delivery else None,
            "demo_steps": [
                "Farmer publishes 1,000 kg Grade A tomatoes.",
                "Buyer requests 2,000 kg Grade A tomatoes within 3 days.",
                "Matching aggregates Ramesh Farm, Kavita Farm, and Sahyadri FPO.",
                "Payment is held in prototype protection.",
                "Transporter accepts pooled Nashik to Mumbai trip.",
                "OR-Tools optimizes the route and shows distance/cost savings.",
                "Pickup and delivery proofs update payment and reputation.",
            ],
        }
    )


@app.get("/data/sources")
def data_sources(db: Session = Depends(get_db)) -> dict:
    rows = db.scalars(select(DataSource).order_by(DataSource.name)).all()
    return api_response(
        [
            {
                "name": row.name,
                "official_source": row.official_source,
                "url": row.url,
                "access_method": row.access_method,
                "format": row.format,
                "fields": row.fields,
                "geographic_coverage": row.geographic_coverage,
                "time_range": row.time_range,
                "update_frequency": row.update_frequency,
                "license": row.license,
                "usable_for_ml": row.usable_for_ml,
                "limitations": row.limitations,
                "data_classification": row.data_classification.value,
            }
            for row in rows
        ]
    )


@app.get("/farmer/home")
def farmer_home(
    lang: str = "en",
    user: User = Depends(require_roles(RoleName.FARMER)),
    db: Session = Depends(get_db),
) -> dict:
    listings = db.scalars(select(ProduceListing).where(ProduceListing.farmer_id == user.id)).all()
    orders = (
        db.scalars(select(Order).join(OrderItem).where(OrderItem.seller_id == user.id).order_by(Order.created_at.desc()))
        .unique()
        .all()
    )
    tomato = get_crop_by_name(db, "Tomato")
    market_price = db.scalar(select(MarketPrice).where(MarketPrice.crop_id == tomato.id).order_by(MarketPrice.created_at.desc()))
    total_expected = sum(listing.quantity_kg * listing.expected_price_per_kg for listing in listings)
    text = {
        "greeting": f"नमस्ते {user.name.split()[0]}" if lang == "hi" else f"Hello {user.name.split()[0]}",
        "sell_button": "फसल बेचें" if lang == "hi" else "Sell Crop",
        "market_label": "आज टमाटर का भाव" if lang == "hi" else "Today's tomato mandi price",
        "earning_label": "अनुमानित बिक्री" if lang == "hi" else "Expected sale value",
        "payment_protected": "भुगतान सुरक्षित है" if lang == "hi" else "Payment protected",
    }
    return api_response(
        {
            "text": text,
            "market_price": {
                "crop": tomato.name,
                "range_per_kg": [
                    round((market_price.min_price if market_price else 2400) / 100, 2),
                    round((market_price.max_price if market_price else 2800) / 100, 2),
                ],
                "unit": "INR/kg",
                "data_classification": "SYNTHETIC_SAMPLE shaped from official schema",
            },
            "active_listings": [serialize_listing(listing) for listing in listings],
            "orders": [serialize_order(order, db) for order in orders],
            "expected_earnings": round(total_expected, 2),
            "alerts": active_alerts_for_user(db, user.id),
        }
    )


@app.post("/farmer/sale-estimate")
def farmer_sale_estimate(
    payload: SaleEstimateRequest,
    _: User = Depends(require_roles(RoleName.FARMER)),
    db: Session = Depends(get_db),
) -> dict:
    estimate = sale_estimate(
        db,
        crop_name=payload.crop,
        quantity_kg=payload.quantity_kg,
        grade=payload.grade,
        available_date=payload.available_date,
    )
    return api_response(estimate)


@app.post("/farmer/listings")
def create_listing(
    payload: ListingCreate,
    user: User = Depends(require_roles(RoleName.FARMER)),
    db: Session = Depends(get_db),
) -> dict:
    crop = get_crop_by_name(db, payload.crop)
    profile = db.scalar(select(FarmerProfile).where(FarmerProfile.user_id == user.id))
    location_id = payload.pickup_location_id
    if not location_id:
        previous_listing = db.scalar(
            select(ProduceListing).where(ProduceListing.farmer_id == user.id).order_by(ProduceListing.created_at.desc())
        )
        fallback_location = previous_listing.location if previous_listing else default_depot(db)
        location_id = fallback_location.id
    estimate = sale_estimate(
        db,
        crop_name=payload.crop,
        quantity_kg=payload.quantity_kg,
        grade=payload.grade,
        available_date=payload.available_date,
    )
    listing = ProduceListing(
        farmer_id=user.id,
        fpo_id=profile.fpo_id if profile else None,
        crop_id=crop.id,
        location_id=location_id,
        quantity_kg=payload.quantity_kg,
        available_date=payload.available_date,
        grade=payload.grade,
        expected_price_per_kg=payload.expected_price_per_kg
        or estimate["recommended_listing_price_per_kg"],
        image_url=payload.image_url,
    )
    db.add(listing)
    db.flush()
    audit(
        db,
        actor_id=user.id,
        action="listing.created",
        entity_type="ProduceListing",
        entity_id=listing.id,
        new_value={"crop": crop.name, "quantity_kg": listing.quantity_kg},
    )
    db.commit()
    db.refresh(listing)
    return api_response({"listing": serialize_listing(listing), "sale_estimate": estimate}, "Listing published")


@app.get("/farmer/listings")
def farmer_listings(
    user: User = Depends(require_roles(RoleName.FARMER)),
    db: Session = Depends(get_db),
) -> dict:
    rows = db.scalars(select(ProduceListing).where(ProduceListing.farmer_id == user.id)).all()
    return api_response([serialize_listing(row) for row in rows])


@app.get("/buyer/marketplace")
def buyer_marketplace(
    user: User = Depends(require_roles(RoleName.BUYER, RoleName.ADMIN)),
    db: Session = Depends(get_db),
) -> dict:
    _ = user
    rows = db.scalars(select(ProduceListing).order_by(ProduceListing.created_at.desc())).all()
    return api_response(
        {
            "filters": ["crop", "quantity", "location", "quality", "verified farmer/FPO", "availability"],
            "listings": [serialize_listing(row) for row in rows],
        }
    )


@app.post("/buyer/requirements")
def create_requirement(
    payload: BuyerRequirementCreate,
    user: User = Depends(require_roles(RoleName.BUYER)),
    db: Session = Depends(get_db),
) -> dict:
    crop = get_crop_by_name(db, payload.crop)
    destination_id = payload.destination_location_id
    if not destination_id:
        latest_requirement = db.scalar(
            select(BuyerRequirement).where(BuyerRequirement.buyer_id == user.id).order_by(BuyerRequirement.created_at.desc())
        )
        destination_id = latest_requirement.destination_location_id if latest_requirement else default_depot(db).id
    requirement = BuyerRequirement(
        buyer_id=user.id,
        crop_id=crop.id,
        destination_location_id=destination_id,
        required_quantity_kg=payload.required_quantity_kg,
        grade=payload.grade,
        needed_by=payload.needed_by,
        max_price_per_kg=payload.max_price_per_kg,
        recurring=payload.recurring,
    )
    db.add(requirement)
    db.flush()
    audit(
        db,
        actor_id=user.id,
        action="requirement.created",
        entity_type="BuyerRequirement",
        entity_id=requirement.id,
        new_value={"crop": crop.name, "quantity_kg": requirement.required_quantity_kg},
    )
    db.commit()
    db.refresh(requirement)
    return api_response(
        {
            "requirement": serialize_requirement(requirement),
            "matches": find_matches(db, requirement),
        },
        "Requirement created",
    )


@app.get("/buyer/requirements")
def buyer_requirements(
    user: User = Depends(require_roles(RoleName.BUYER)),
    db: Session = Depends(get_db),
) -> dict:
    rows = db.scalars(select(BuyerRequirement).where(BuyerRequirement.buyer_id == user.id)).all()
    return api_response([serialize_requirement(row) for row in rows])


@app.get("/buyer/requirements/{requirement_id}/matches")
def buyer_matches(
    requirement_id: str,
    user: User = Depends(require_roles(RoleName.BUYER, RoleName.ADMIN)),
    db: Session = Depends(get_db),
) -> dict:
    requirement = db.get(BuyerRequirement, requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    if RoleName.ADMIN.value not in roles_for_user(user) and requirement.buyer_id != user.id:
        raise HTTPException(status_code=403, detail="Cannot view another buyer's requirement")
    return api_response(find_matches(db, requirement))


@app.post("/buyer/requirements/{requirement_id}/order")
def create_order_from_requirement(
    requirement_id: str,
    paid_amount: float | None = None,
    user: User = Depends(require_roles(RoleName.BUYER)),
    db: Session = Depends(get_db),
) -> dict:
    try:
        result = create_protected_order_from_requirement(
            db,
            requirement_id=requirement_id,
            buyer=user,
            paid_amount=paid_amount,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    db.commit()
    db.refresh(result["order"])
    db.refresh(result["delivery"])
    return api_response(
        {
            "order": serialize_order(result["order"], db),
            "payment": serialize_payment(result["payment"]),
            "delivery": serialize_delivery(result["delivery"]),
            "matches": result["matches"],
        },
        "Order created and payment protection simulated",
    )


@app.get("/buyer/orders")
def buyer_orders(
    user: User = Depends(require_roles(RoleName.BUYER)),
    db: Session = Depends(get_db),
) -> dict:
    orders = db.scalars(select(Order).where(Order.buyer_id == user.id).order_by(Order.created_at.desc())).all()
    return api_response([serialize_order(order, db) for order in orders])


@app.post("/buyer/deliveries/{delivery_id}/confirm")
def confirm_delivery(
    delivery_id: str,
    payload: DeliveryConfirmRequest,
    user: User = Depends(require_roles(RoleName.BUYER)),
    db: Session = Depends(get_db),
) -> dict:
    delivery = db.get(Delivery, delivery_id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    order = delivery.order
    if order.buyer_id != user.id:
        raise HTTPException(status_code=403, detail="Cannot confirm another buyer's delivery")

    record = DeliveryRecord(
        delivery_id=delivery.id,
        buyer_id=user.id,
        expected_quantity_kg=delivery.cargo_kg,
        delivered_quantity_kg=payload.delivered_quantity_kg,
        decision=payload.decision,
        digital_signature=payload.digital_signature,
        photo_url=payload.photo_url,
        notes=payload.notes,
    )
    db.add(record)
    payment = db.scalar(select(Payment).where(Payment.order_id == order.id))
    release_amount = 0.0
    if payload.decision == "Accepted":
        release_amount = payment.held_amount if payment else 0
        delivery.status = DeliveryStatus.DELIVERED
        order.status = OrderStatus.COMPLETED
        order.payment_status = PaymentStatus.RELEASED
        if payment:
            payment.status = PaymentStatus.RELEASED
    elif payload.decision == "Partially Accepted":
        accepted_ratio = min(1.0, payload.delivered_quantity_kg / delivery.cargo_kg) if delivery.cargo_kg else 0
        release_amount = round((payment.held_amount if payment else 0) * accepted_ratio, 2)
        delivery.status = DeliveryStatus.DISPUTED
        order.status = OrderStatus.DISPUTED
        order.payment_status = PaymentStatus.PARTIAL_RELEASED
        if payment:
            payment.status = PaymentStatus.PARTIAL_RELEASED
        db.add(
            Dispute(
                order_id=order.id,
                delivery_id=delivery.id,
                opened_by_id=user.id,
                dispute_type="PARTIAL_DELIVERY",
                description="Buyer accepted partial quantity; admin review required for balance.",
                evidence={"delivered_quantity_kg": payload.delivered_quantity_kg, "notes": payload.notes},
            )
        )
    else:
        delivery.status = DeliveryStatus.DISPUTED
        order.status = OrderStatus.DISPUTED
        order.payment_status = PaymentStatus.DISPUTED
        if payment:
            payment.status = PaymentStatus.DISPUTED
        db.add(
            Dispute(
                order_id=order.id,
                delivery_id=delivery.id,
                opened_by_id=user.id,
                dispute_type="QUALITY_REJECTION",
                description="Buyer rejected produce; payment remains on hold for admin review.",
                evidence={"notes": payload.notes, "photo_url": payload.photo_url},
            )
        )

    if payment and release_amount:
        payment.released_amount = round(payment.released_amount + release_amount, 2)
        payment.held_amount = round(max(0, payment.held_amount - release_amount), 2)
        db.add(PaymentRelease(payment_id=payment.id, amount=release_amount, reason=f"Buyer decision: {payload.decision}"))
    buyer_stop = next((stop for stop in delivery.stops if stop.stop_type == "BUYER"), None)
    if buyer_stop:
        buyer_stop.actual_quantity_kg = payload.delivered_quantity_kg
        buyer_stop.status = StopStatus.DELIVERED if payload.decision != "Rejected" else StopStatus.PENDING
    audit(
        db,
        actor_id=user.id,
        action="delivery.confirmed",
        entity_type="Delivery",
        entity_id=delivery.id,
        new_value={"decision": payload.decision, "release_amount": release_amount},
    )
    db.commit()
    db.refresh(delivery)
    return api_response(
        {
            "delivery": serialize_delivery(delivery),
            "delivery_record_id": record.id,
            "payment": serialize_payment(payment),
            "release_amount": release_amount,
        },
        "Delivery confirmation recorded",
    )


@app.get("/transporter/trips/available")
def available_trips(
    _: User = Depends(require_roles(RoleName.TRANSPORTER, RoleName.ADMIN)),
    db: Session = Depends(get_db),
) -> dict:
    deliveries = db.scalars(
        select(Delivery).where(Delivery.status == DeliveryStatus.REQUESTED).order_by(Delivery.created_at.desc())
    ).all()
    return api_response([serialize_delivery(delivery) for delivery in deliveries])


@app.post("/transporter/trips/{delivery_id}/accept")
def accept_trip(
    delivery_id: str,
    user: User = Depends(require_roles(RoleName.TRANSPORTER)),
    db: Session = Depends(get_db),
) -> dict:
    delivery = db.get(Delivery, delivery_id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    if delivery.status not in {DeliveryStatus.REQUESTED, DeliveryStatus.ACCEPTED}:
        raise HTTPException(status_code=400, detail="Delivery cannot be accepted in current status")
    vehicles = demo_vehicle_capacities(db, transporter_id=user.id)
    route = create_route_for_order(db, delivery.order, vehicles=vehicles)
    vehicle_id = vehicles[0].id if vehicles else None
    delivery.transporter_id = user.id
    delivery.vehicle_id = vehicle_id
    delivery.route_id = route.id
    delivery.status = DeliveryStatus.ACCEPTED
    delivery.estimated_distance_km = route.optimized_distance_km
    delivery.estimated_duration_hours = route.route_payload.get("estimated_duration_hours", delivery.estimated_duration_hours)
    delivery.estimated_earnings = round(route.optimized_distance_km * 24, 2)
    db.add(
        RouteEvent(
            delivery_id=delivery.id,
            actor_id=user.id,
            event_type="TRIP_ACCEPTED",
            payload={"vehicle_id": vehicle_id, "route_id": route.id},
        )
    )
    audit(
        db,
        actor_id=user.id,
        action="delivery.accepted",
        entity_type="Delivery",
        entity_id=delivery.id,
        new_value={"route_id": route.id, "vehicle_id": vehicle_id},
    )
    db.commit()
    db.refresh(delivery)
    return api_response(serialize_delivery(delivery), "Trip accepted and route optimized")


@app.get("/transporter/active")
def active_delivery(
    user: User = Depends(require_roles(RoleName.TRANSPORTER)),
    db: Session = Depends(get_db),
) -> dict:
    delivery = db.scalar(
        select(Delivery)
        .where(Delivery.transporter_id == user.id, Delivery.status != DeliveryStatus.DELIVERED)
        .order_by(Delivery.updated_at.desc())
    )
    return api_response(serialize_delivery(delivery) if delivery else None)


@app.post("/transporter/deliveries/{delivery_id}/pickup")
def confirm_pickup(
    delivery_id: str,
    payload: PickupConfirmRequest,
    user: User = Depends(require_roles(RoleName.TRANSPORTER)),
    db: Session = Depends(get_db),
) -> dict:
    delivery = db.get(Delivery, delivery_id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    if delivery.transporter_id and delivery.transporter_id != user.id:
        raise HTTPException(status_code=403, detail="Delivery is assigned to another transporter")
    stop = db.get(DeliveryStop, payload.stop_id)
    if not stop or stop.delivery_id != delivery.id or stop.stop_type != "PICKUP":
        raise HTTPException(status_code=400, detail="Pickup stop not found for this delivery")
    stop.actual_quantity_kg = payload.actual_quantity_kg
    stop.status = StopStatus.PICKED_UP
    delivery.status = DeliveryStatus.PICKED_UP
    record = PickupRecord(
        delivery_id=delivery.id,
        stop_id=stop.id,
        transporter_id=user.id,
        expected_quantity_kg=stop.planned_quantity_kg,
        actual_quantity_kg=payload.actual_quantity_kg,
        grade=payload.grade,
        photo_url=payload.photo_url,
        weighing_slip_url=payload.weighing_slip_url,
        notes=payload.notes,
    )
    db.add(record)
    db.add(
        RouteEvent(
            delivery_id=delivery.id,
            actor_id=user.id,
            event_type="PICKUP_CONFIRMED",
            location_id=stop.location_id,
            payload={"actual_quantity_kg": payload.actual_quantity_kg, "grade": payload.grade},
        )
    )
    audit(
        db,
        actor_id=user.id,
        action="pickup.confirmed",
        entity_type="DeliveryStop",
        entity_id=stop.id,
        new_value={"actual_quantity_kg": payload.actual_quantity_kg},
    )
    if all(s.status == StopStatus.PICKED_UP for s in delivery.stops if s.stop_type == "PICKUP"):
        delivery.status = DeliveryStatus.IN_TRANSIT
        delivery.order.status = OrderStatus.IN_TRANSIT
    db.commit()
    db.refresh(delivery)
    return api_response({"delivery": serialize_delivery(delivery), "pickup_record_id": record.id}, "Pickup recorded")


@app.post("/transporter/deliveries/{delivery_id}/incident")
def report_incident(
    delivery_id: str,
    payload: IncidentCreate,
    user: User = Depends(require_roles(RoleName.TRANSPORTER)),
    db: Session = Depends(get_db),
) -> dict:
    delivery = db.get(Delivery, delivery_id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    incident = Incident(
        delivery_id=delivery.id,
        reported_by_id=user.id,
        incident_type=payload.incident_type,
        description=payload.description,
        latitude=payload.latitude,
        longitude=payload.longitude,
        evidence_urls=payload.evidence_urls,
    )
    delivery.status = DeliveryStatus.INCIDENT_REPORTED
    db.add(incident)
    audit(
        db,
        actor_id=user.id,
        action="incident.reported",
        entity_type="Incident",
        entity_id=incident.id,
        new_value={"type": payload.incident_type},
    )
    db.commit()
    return api_response({"incident_id": incident.id, "status": incident.status}, "Incident submitted for admin review")


@app.post("/routes/optimize")
def optimize_route(
    payload: RouteOptimizeRequest,
    _: User = Depends(require_roles(RoleName.TRANSPORTER, RoleName.ADMIN)),
) -> dict:
    result = optimize_cvrp(
        depot=payload.depot,
        pickups=payload.pickups,
        buyer=payload.buyer,
        vehicles=payload.vehicles,
        cost_per_km=payload.cost_per_km,
        deadline_hours=payload.deadline_hours,
    )
    return api_response(result)


@app.post("/ml/price/predict")
def ml_price_predict(
    payload: SaleEstimateRequest,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    result = price_prediction(db, payload.crop, horizon_days=max(1, (payload.available_date - date.today()).days))
    db.commit()
    return api_response(result)


@app.post("/ml/demand/predict")
def ml_demand_predict(
    payload: DemandPredictRequest,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    result = demand_prediction(db, payload.crop, payload.region, payload.horizon_days)
    db.commit()
    return api_response(result)


@app.post("/ml/quality/predict")
def ml_quality_predict(
    payload: QualityPredictRequest,
    _: User = Depends(get_current_user),
) -> dict:
    if payload.crop.lower() != "tomato":
        return api_response(
            {
                "supported": False,
                "message": "MVP quality demo is intentionally limited to tomato.",
                "disclaimer": "Quality should be verified by declared grade, inspection, and transaction history.",
            }
        )
    confidence = 0.78 if payload.image_url else 0.58
    return api_response(
        {
            "supported": True,
            "crop": payload.crop,
            "declared_grade": payload.declared_grade.value,
            "ai_estimated_grade": payload.declared_grade.value,
            "confidence": confidence,
            "method": "AI-assisted quality estimate demo; not a universal grading model",
            "next_step": "Require transporter/buyer inspection evidence before payment release.",
        }
    )


@app.post("/ml/match/score")
def ml_match_score(
    payload: MatchScoreRequest,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    requirement = db.get(BuyerRequirement, payload.requirement_id)
    listing = db.get(ProduceListing, payload.listing_id)
    if not requirement or not listing:
        raise HTTPException(status_code=404, detail="Requirement or listing not found")
    return api_response(score_listing(db, requirement, listing))


@app.get("/notifications")
def notifications(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    rows = db.scalars(select(Notification).where(Notification.user_id == user.id).order_by(Notification.created_at.desc())).all()
    return api_response(
        [
            {
                "id": row.id,
                "type": row.notification_type,
                "title": row.title,
                "message": row.message,
                "created_at": row.created_at.isoformat(),
                "read": row.read_at is not None,
            }
            for row in rows
        ]
    )


@app.get("/admin/dashboard")
def admin_dashboard(
    _: User = Depends(require_roles(RoleName.ADMIN)),
    db: Session = Depends(get_db),
) -> dict:
    role_counts = {
        role.value: db.scalar(select(func.count(Role.id)).where(Role.name == role)) or 0
        for role in [RoleName.FARMER, RoleName.BUYER, RoleName.TRANSPORTER, RoleName.ADMIN]
    }
    orders = db.scalars(select(Order)).all()
    deliveries = db.scalars(select(Delivery)).all()
    disputes = db.scalars(select(Dispute).order_by(Dispute.created_at.desc())).all()
    route_savings = sum(delivery.route.saved_distance_km for delivery in deliveries if delivery.route)
    return api_response(
        {
            "kpis": {
                "total_farmers": role_counts["FARMER"],
                "total_buyers": role_counts["BUYER"],
                "total_transporters": role_counts["TRANSPORTER"],
                "active_orders": sum(1 for order in orders if order.status != OrderStatus.COMPLETED),
                "completed_orders": sum(1 for order in orders if order.status == OrderStatus.COMPLETED),
                "pending_disputes": len([d for d in disputes if d.status == "UNDER_REVIEW"]),
                "total_produce_kg": sum(order.total_quantity_kg for order in orders),
                "total_transaction_value": round(sum(order.total_value for order in orders), 2),
                "route_savings_km": round(route_savings, 2),
                "average_farmer_realization_per_kg": round(
                    sum(item.price_per_kg for order in orders for item in order.items)
                    / max(1, sum(len(order.items) for order in orders)),
                    2,
                ),
            },
            "ai_dashboard": {
                "price_forecast": price_prediction(db, "Tomato", 7),
                "demand_forecast": demand_prediction(db, "Tomato", "Nashik-Mumbai", 5),
                "glut_alerts": [
                    {"title": alert.title, "severity": alert.severity}
                    for alert in db.scalars(select(Alert).where(Alert.alert_type == "SUPPLY_GLUT")).all()
                ],
            },
            "disputes": [
                {
                    "id": dispute.id,
                    "type": dispute.dispute_type,
                    "status": dispute.status,
                    "description": dispute.description,
                }
                for dispute in disputes
            ],
            "system_health": {"api": "ok", "database": "ok", "ml": "demo baseline", "routing": "OR-Tools active"},
        }
    )


@app.get("/admin/matching-weights")
def get_matching_weights(_: User = Depends(require_roles(RoleName.ADMIN))) -> dict:
    return api_response(MATCHING_WEIGHTS)


@app.post("/admin/matching-weights")
def update_matching_weights(
    payload: MatchingWeightsUpdate,
    user: User = Depends(require_roles(RoleName.ADMIN)),
    db: Session = Depends(get_db),
) -> dict:
    incoming = payload.model_dump()
    total = sum(incoming.values())
    if total <= 0:
        raise HTTPException(status_code=400, detail="Weights must have a positive total")
    old = MATCHING_WEIGHTS.copy()
    for key, value in incoming.items():
        MATCHING_WEIGHTS[key] = round(value / total, 4)
    audit(
        db,
        actor_id=user.id,
        action="admin.matching_weights_updated",
        entity_type="MatchingWeights",
        old_value=old,
        new_value=MATCHING_WEIGHTS.copy(),
    )
    db.commit()
    return api_response(MATCHING_WEIGHTS, "Matching weights updated")


@app.get("/admin/audit-logs")
def audit_logs(
    _: User = Depends(require_roles(RoleName.ADMIN)),
    db: Session = Depends(get_db),
) -> dict:
    from backend.app.models import AuditLog

    rows = db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(80)).all()
    return api_response(
        [
            {
                "id": row.id,
                "actor_id": row.actor_id,
                "action": row.action,
                "entity_type": row.entity_type,
                "entity_id": row.entity_id,
                "old_value": row.old_value,
                "new_value": row.new_value,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]
    )


@app.get("/admin/state-rules")
def state_rules(_: User = Depends(require_roles(RoleName.ADMIN)), db: Session = Depends(get_db)) -> dict:
    rows = db.scalars(select(StateRule).order_by(StateRule.state)).all()
    return api_response(
        [
            {
                "id": row.id,
                "state": row.state,
                "market_type": row.market_type,
                "mandi_requirements": row.mandi_requirements,
                "direct_sale_allowed": row.direct_sale_allowed,
                "documentation_requirements": row.documentation_requirements,
                "special_rules": row.special_rules,
                "data_classification": row.data_classification.value,
            }
            for row in rows
        ]
    )
