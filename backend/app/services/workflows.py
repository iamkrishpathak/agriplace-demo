from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models import (
    DataClass,
    Delivery,
    DeliveryStatus,
    DeliveryStop,
    Location,
    ListingStatus,
    Order,
    OrderItem,
    OrderStatus,
    Payment,
    PaymentHold,
    PaymentStatus,
    ProduceListing,
    RequirementStatus,
    RoutePlan,
    StopStatus,
    User,
    Vehicle,
)
from backend.app.schemas import RouteLocation, VehicleCapacity
from backend.app.services.audit import audit
from backend.app.services.matching import find_matches
from backend.app.services.routing import optimize_cvrp


def next_order_number(db: Session) -> str:
    count = db.scalar(select(func.count(Order.id))) or 0
    return f"AGP-{1001 + count}"


def default_depot(db: Session) -> Location:
    depot = db.scalar(select(Location).where(Location.location_type == "DEPOT"))
    if not depot:
        depot = Location(
            label="AgriPlace Nashik Pooling Depot",
            address="Nashik logistics pooling point",
            district="Nashik",
            state="Maharashtra",
            latitude=19.9975,
            longitude=73.7898,
            location_type="DEPOT",
            data_classification=DataClass.SYNTHETIC,
        )
        db.add(depot)
        db.flush()
    return depot


def demo_vehicle_capacities(db: Session, transporter_id: str | None = None) -> list[VehicleCapacity]:
    stmt = select(Vehicle).order_by(Vehicle.capacity_kg.desc())
    if transporter_id:
        stmt = stmt.where(Vehicle.transporter.has(user_id=transporter_id))
    vehicles = list(db.scalars(stmt).all())
    if not vehicles:
        return [VehicleCapacity(id=None, label="Mini Truck", capacity_kg=2000)]
    return [
        VehicleCapacity(
            id=vehicle.id,
            label=f"{vehicle.vehicle_type} {vehicle.registration_number}",
            capacity_kg=int(vehicle.capacity_kg),
        )
        for vehicle in vehicles[:2]
    ]


def order_pickup_locations(order: Order) -> list[RouteLocation]:
    return [
        RouteLocation(
            id=item.listing.location.id,
            label=f"{item.seller.name} - {item.crop.name}",
            latitude=item.listing.location.latitude,
            longitude=item.listing.location.longitude,
            quantity_kg=item.quantity_kg,
            stop_type="PICKUP",
        )
        for item in order.items
    ]


def buyer_route_location(order: Order) -> RouteLocation:
    destination = order.items[0].order.requirement.destination if order.requirement_id else None
    if destination is None:
        raise ValueError("Order does not have a destination")
    return RouteLocation(
        id=destination.id,
        label=destination.label,
        latitude=destination.latitude,
        longitude=destination.longitude,
        quantity_kg=0,
        stop_type="BUYER",
    )


def create_route_for_order(
    db: Session,
    order: Order,
    *,
    vehicles: list[VehicleCapacity] | None = None,
) -> RoutePlan:
    depot = default_depot(db)
    payload = optimize_cvrp(
        depot=RouteLocation(
            id=depot.id,
            label=depot.label,
            latitude=depot.latitude,
            longitude=depot.longitude,
            stop_type="DEPOT",
        ),
        pickups=order_pickup_locations(order),
        buyer=buyer_route_location(order),
        vehicles=vehicles or demo_vehicle_capacities(db),
        cost_per_km=24,
        deadline_hours=12,
    )
    route = RoutePlan(
        provider=payload.get("provider", "derived-haversine-demo"),
        original_distance_km=payload.get("original_distance_km", 0),
        optimized_distance_km=payload.get("optimized_distance_km", 0),
        saved_distance_km=payload.get("saved_distance_km", 0),
        estimated_cost_saving=payload.get("estimated_cost_saving", 0),
        route_payload=payload,
    )
    db.add(route)
    db.flush()
    return route


def create_delivery_for_order(db: Session, order: Order, route: RoutePlan) -> Delivery:
    delivery = Delivery(
        order_id=order.id,
        route_id=route.id,
        status=DeliveryStatus.REQUESTED,
        cargo_kg=order.total_quantity_kg,
        estimated_distance_km=route.optimized_distance_km or route.original_distance_km,
        estimated_duration_hours=route.route_payload.get("estimated_duration_hours", 0),
        estimated_earnings=round((route.optimized_distance_km or 170) * 24, 2),
    )
    db.add(delivery)
    db.flush()

    sequence = 1
    for item in order.items:
        db.add(
            DeliveryStop(
                delivery_id=delivery.id,
                listing_id=item.listing_id,
                location_id=item.listing.location_id,
                stop_type="PICKUP",
                sequence=sequence,
                planned_quantity_kg=item.quantity_kg,
                status=StopStatus.PENDING,
            )
        )
        sequence += 1

    destination = order.items[0].order.requirement.destination
    db.add(
        DeliveryStop(
            delivery_id=delivery.id,
            location_id=destination.id,
            stop_type="BUYER",
            sequence=sequence,
            planned_quantity_kg=order.total_quantity_kg,
            status=StopStatus.PENDING,
        )
    )
    db.flush()
    return delivery


def create_protected_order_from_requirement(
    db: Session,
    *,
    requirement_id: str,
    buyer: User,
    paid_amount: float | None = None,
) -> dict:
    from backend.app.models import BuyerRequirement

    requirement = db.get(BuyerRequirement, requirement_id)
    if not requirement:
        raise ValueError("Requirement not found")
    if requirement.buyer_id != buyer.id:
        raise PermissionError("Cannot create order for another buyer")

    matches = find_matches(db, requirement, persist=True)
    if not matches["matches"]:
        raise ValueError("No suitable listings are available")

    total_value = round(
        sum(match["quantity_kg"] * match["price_per_kg"] for match in matches["matches"]),
        2,
    )
    paid = total_value if paid_amount is None else min(paid_amount, total_value)
    payment_status = PaymentStatus.HELD if paid >= total_value else PaymentStatus.PARTIAL_PAYMENT
    order_status = OrderStatus.PAYMENT_PROTECTED if payment_status == PaymentStatus.HELD else OrderStatus.PAYMENT_PENDING

    order = Order(
        order_number=next_order_number(db),
        buyer_id=buyer.id,
        requirement_id=requirement.id,
        status=order_status,
        payment_status=payment_status,
        total_quantity_kg=matches["matched_quantity_kg"],
        total_value=total_value,
    )
    db.add(order)
    db.flush()

    for match in matches["matches"]:
        listing = db.get(ProduceListing, match["listing_id"])
        if not listing:
            continue
        db.add(
            OrderItem(
                order_id=order.id,
                listing_id=listing.id,
                seller_id=listing.farmer_id,
                crop_id=listing.crop_id,
                quantity_kg=match["quantity_kg"],
                price_per_kg=match["price_per_kg"],
            )
        )
        listing.status = ListingStatus.MATCHED

    requirement.status = RequirementStatus.ORDERED
    db.flush()
    db.refresh(order)

    payment = Payment(
        order_id=order.id,
        buyer_id=buyer.id,
        status=payment_status,
        amount=total_value,
        paid_amount=paid,
        held_amount=paid,
        released_amount=0,
        remaining_amount=round(total_value - paid, 2),
    )
    db.add(payment)
    db.flush()
    db.add(
        PaymentHold(
            payment_id=payment.id,
            amount=paid,
            reason="Buyer checkout created a prototype protected payment hold",
        )
    )

    route = create_route_for_order(db, order)
    delivery = create_delivery_for_order(db, order, route)
    audit(
        db,
        actor_id=buyer.id,
        action="order.created_with_payment_hold",
        entity_type="Order",
        entity_id=order.id,
        new_value={"order_number": order.order_number, "payment_status": payment_status.value},
    )
    db.flush()
    return {"order": order, "payment": payment, "delivery": delivery, "matches": matches}
