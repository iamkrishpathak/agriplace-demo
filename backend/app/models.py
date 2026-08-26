import enum
import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy import JSON as SAJSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base


def new_uuid() -> str:
    return str(uuid.uuid4())


class RoleName(str, enum.Enum):
    FARMER = "FARMER"
    BUYER = "BUYER"
    TRANSPORTER = "TRANSPORTER"
    ADMIN = "ADMIN"


class UserStatus(str, enum.Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    SUSPENDED = "SUSPENDED"


class ListingStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    MATCHED = "MATCHED"
    CANCELLED = "CANCELLED"
    SOLD = "SOLD"


class RequirementStatus(str, enum.Enum):
    OPEN = "OPEN"
    MATCHED = "MATCHED"
    ORDERED = "ORDERED"
    CANCELLED = "CANCELLED"


class OrderStatus(str, enum.Enum):
    CREATED = "CREATED"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PAYMENT_PROTECTED = "PAYMENT_PROTECTED"
    PICKUP_IN_PROGRESS = "PICKUP_IN_PROGRESS"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    COMPLETED = "COMPLETED"
    DISPUTED = "DISPUTED"
    CANCELLED = "CANCELLED"


class PaymentStatus(str, enum.Enum):
    NOT_PAID = "NOT_PAID"
    PARTIAL_PAYMENT = "PARTIAL_PAYMENT"
    HELD = "HELD"
    RELEASED = "RELEASED"
    PARTIAL_RELEASED = "PARTIAL_RELEASED"
    DISPUTED = "DISPUTED"


class DeliveryStatus(str, enum.Enum):
    REQUESTED = "REQUESTED"
    ACCEPTED = "ACCEPTED"
    ARRIVED = "ARRIVED"
    PICKUP_IN_PROGRESS = "PICKUP_IN_PROGRESS"
    PICKED_UP = "PICKED_UP"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    INCIDENT_REPORTED = "INCIDENT_REPORTED"
    DISPUTED = "DISPUTED"


class StopStatus(str, enum.Enum):
    PENDING = "PENDING"
    ARRIVED = "ARRIVED"
    QUANTITY_VERIFIED = "QUANTITY_VERIFIED"
    LOADED = "LOADED"
    PICKED_UP = "PICKED_UP"
    DELIVERED = "DELIVERED"
    SKIPPED = "SKIPPED"


class Grade(str, enum.Enum):
    A = "Grade A"
    B = "Grade B"
    C = "Grade C"


class DataClass(str, enum.Enum):
    REAL = "REAL"
    SYNTHETIC = "SYNTHETIC"
    DERIVED = "DERIVED"
    PROXY = "PROXY"
    SOURCE_READY = "SOURCE_READY"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(24), unique=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    preferred_language: Mapped[str] = mapped_column(String(8), default="en", nullable=False)
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, native_enum=False), default=UserStatus.VERIFIED, nullable=False
    )

    roles: Mapped[list["Role"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    farmer_profile: Mapped["FarmerProfile | None"] = relationship(back_populates="user")
    buyer_profile: Mapped["BuyerProfile | None"] = relationship(back_populates="user")
    transporter_profile: Mapped["TransporterProfile | None"] = relationship(back_populates="user")


class Role(Base):
    __tablename__ = "roles"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_user_role"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[RoleName] = mapped_column(Enum(RoleName, native_enum=False), nullable=False)

    user: Mapped[User] = relationship(back_populates="roles")


class FarmerProfile(Base, TimestampMixin):
    __tablename__ = "farmer_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    village: Mapped[str] = mapped_column(String(120), nullable=False)
    district: Mapped[str] = mapped_column(String(120), nullable=False)
    state: Mapped[str] = mapped_column(String(120), nullable=False)
    land_acres: Mapped[float] = mapped_column(Float, default=2.0, nullable=False)
    fpo_id: Mapped[str | None] = mapped_column(ForeignKey("fpo_profiles.id"))
    verification_status: Mapped[str] = mapped_column(String(32), default="VERIFIED", nullable=False)

    user: Mapped[User] = relationship(back_populates="farmer_profile")
    fpo: Mapped["FPOProfile | None"] = relationship(back_populates="farmers")


class BuyerProfile(Base, TimestampMixin):
    __tablename__ = "buyer_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    buyer_type: Mapped[str] = mapped_column(String(80), nullable=False)
    business_name: Mapped[str] = mapped_column(String(160), nullable=False)
    gstin: Mapped[str | None] = mapped_column(String(32))
    verification_status: Mapped[str] = mapped_column(String(32), default="VERIFIED", nullable=False)

    user: Mapped[User] = relationship(back_populates="buyer_profile")


class TransporterProfile(Base, TimestampMixin):
    __tablename__ = "transporter_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    company_name: Mapped[str] = mapped_column(String(160), nullable=False)
    license_number: Mapped[str] = mapped_column(String(80), nullable=False)
    verification_status: Mapped[str] = mapped_column(String(32), default="VERIFIED", nullable=False)

    user: Mapped[User] = relationship(back_populates="transporter_profile")
    vehicles: Mapped[list["Vehicle"]] = relationship(back_populates="transporter")


class FPOProfile(Base, TimestampMixin):
    __tablename__ = "fpo_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    registration_number: Mapped[str] = mapped_column(String(80), nullable=False)
    district: Mapped[str] = mapped_column(String(120), nullable=False)
    state: Mapped[str] = mapped_column(String(120), nullable=False)

    farmers: Mapped[list[FarmerProfile]] = relationship(back_populates="fpo")


class Location(Base, TimestampMixin):
    __tablename__ = "locations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    label: Mapped[str] = mapped_column(String(160), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    district: Mapped[str] = mapped_column(String(120), nullable=False)
    state: Mapped[str] = mapped_column(String(120), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    location_type: Mapped[str] = mapped_column(String(80), nullable=False)
    data_classification: Mapped[DataClass] = mapped_column(
        Enum(DataClass, native_enum=False), default=DataClass.SYNTHETIC, nullable=False
    )


class CollectionCenter(Base, TimestampMixin):
    __tablename__ = "collection_centers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    center_type: Mapped[str] = mapped_column(String(80), nullable=False)
    location_id: Mapped[str] = mapped_column(ForeignKey("locations.id"), nullable=False)
    capacity_kg: Mapped[float] = mapped_column(Float, nullable=False)
    operating_hours: Mapped[str] = mapped_column(String(80), nullable=False)
    services: Mapped[list[str]] = mapped_column(SAJSON, default=list, nullable=False)

    location: Mapped[Location] = relationship()


class Crop(Base, TimestampMixin):
    __tablename__ = "crops"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    hindi_name: Mapped[str] = mapped_column(String(120), nullable=False)
    perishability: Mapped[str] = mapped_column(String(40), default="MEDIUM", nullable=False)


class CropVariety(Base):
    __tablename__ = "crop_varieties"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    crop_id: Mapped[str] = mapped_column(ForeignKey("crops.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    data_classification: Mapped[DataClass] = mapped_column(
        Enum(DataClass, native_enum=False), default=DataClass.SYNTHETIC, nullable=False
    )

    crop: Mapped[Crop] = relationship()


class ProduceListing(Base, TimestampMixin):
    __tablename__ = "produce_listings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    farmer_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    fpo_id: Mapped[str | None] = mapped_column(ForeignKey("fpo_profiles.id"))
    crop_id: Mapped[str] = mapped_column(ForeignKey("crops.id"), nullable=False)
    location_id: Mapped[str] = mapped_column(ForeignKey("locations.id"), nullable=False)
    quantity_kg: Mapped[float] = mapped_column(Float, nullable=False)
    available_date: Mapped[date] = mapped_column(Date, nullable=False)
    grade: Mapped[Grade] = mapped_column(Enum(Grade, native_enum=False), nullable=False)
    status: Mapped[ListingStatus] = mapped_column(
        Enum(ListingStatus, native_enum=False), default=ListingStatus.ACTIVE, nullable=False
    )
    expected_price_per_kg: Mapped[float] = mapped_column(Float, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(255))
    harvest_time: Mapped[datetime | None] = mapped_column(DateTime)
    pickup_deadline: Mapped[datetime | None] = mapped_column(DateTime)
    max_transit_hours: Mapped[float | None] = mapped_column(Float)
    storage_requirement: Mapped[str | None] = mapped_column(String(120))
    temperature_requirement: Mapped[str | None] = mapped_column(String(120))
    data_classification: Mapped[DataClass] = mapped_column(
        Enum(DataClass, native_enum=False), default=DataClass.SYNTHETIC, nullable=False
    )

    farmer: Mapped[User] = relationship()
    crop: Mapped[Crop] = relationship()
    location: Mapped[Location] = relationship()


class ProduceBatch(Base, TimestampMixin):
    __tablename__ = "produce_batches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    listing_id: Mapped[str] = mapped_column(ForeignKey("produce_listings.id"), nullable=False)
    batch_code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    quantity_kg: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="AVAILABLE", nullable=False)

    listing: Mapped[ProduceListing] = relationship()


class QualityRecord(Base, TimestampMixin):
    __tablename__ = "quality_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    listing_id: Mapped[str] = mapped_column(ForeignKey("produce_listings.id"), nullable=False)
    declared_grade: Mapped[Grade] = mapped_column(Enum(Grade, native_enum=False), nullable=False)
    ai_estimated_grade: Mapped[str | None] = mapped_column(String(40))
    inspector_grade: Mapped[str | None] = mapped_column(String(40))
    confidence: Mapped[float | None] = mapped_column(Float)
    notes: Mapped[str | None] = mapped_column(Text)

    listing: Mapped[ProduceListing] = relationship()


class BuyerRequirement(Base, TimestampMixin):
    __tablename__ = "buyer_requirements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    buyer_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    crop_id: Mapped[str] = mapped_column(ForeignKey("crops.id"), nullable=False)
    destination_location_id: Mapped[str] = mapped_column(ForeignKey("locations.id"), nullable=False)
    required_quantity_kg: Mapped[float] = mapped_column(Float, nullable=False)
    grade: Mapped[Grade] = mapped_column(Enum(Grade, native_enum=False), nullable=False)
    needed_by: Mapped[date] = mapped_column(Date, nullable=False)
    max_price_per_kg: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[RequirementStatus] = mapped_column(
        Enum(RequirementStatus, native_enum=False), default=RequirementStatus.OPEN, nullable=False
    )
    recurring: Mapped[bool] = mapped_column(default=False, nullable=False)

    buyer: Mapped[User] = relationship()
    crop: Mapped[Crop] = relationship()
    destination: Mapped[Location] = relationship()


class OrderMatch(Base, TimestampMixin):
    __tablename__ = "order_matches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    requirement_id: Mapped[str] = mapped_column(ForeignKey("buyer_requirements.id"), nullable=False)
    listing_id: Mapped[str] = mapped_column(ForeignKey("produce_listings.id"), nullable=False)
    quantity_kg: Mapped[float] = mapped_column(Float, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    score_breakdown: Mapped[dict[str, Any]] = mapped_column(SAJSON, nullable=False)

    requirement: Mapped[BuyerRequirement] = relationship()
    listing: Mapped[ProduceListing] = relationship()


class Bid(Base, TimestampMixin):
    __tablename__ = "bids"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    buyer_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    listing_id: Mapped[str] = mapped_column(ForeignKey("produce_listings.id"), nullable=False)
    quantity_kg: Mapped[float] = mapped_column(Float, nullable=False)
    price_per_kg: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="OFFERED", nullable=False)


class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    order_number: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    buyer_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    requirement_id: Mapped[str | None] = mapped_column(ForeignKey("buyer_requirements.id"))
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, native_enum=False), default=OrderStatus.CREATED, nullable=False
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, native_enum=False), default=PaymentStatus.NOT_PAID, nullable=False
    )
    total_quantity_kg: Mapped[float] = mapped_column(Float, nullable=False)
    total_value: Mapped[float] = mapped_column(Float, nullable=False)
    data_classification: Mapped[DataClass] = mapped_column(
        Enum(DataClass, native_enum=False), default=DataClass.SYNTHETIC, nullable=False
    )

    buyer: Mapped[User] = relationship()
    requirement: Mapped[BuyerRequirement | None] = relationship()
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base, TimestampMixin):
    __tablename__ = "order_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"), nullable=False)
    listing_id: Mapped[str] = mapped_column(ForeignKey("produce_listings.id"), nullable=False)
    seller_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    crop_id: Mapped[str] = mapped_column(ForeignKey("crops.id"), nullable=False)
    quantity_kg: Mapped[float] = mapped_column(Float, nullable=False)
    price_per_kg: Mapped[float] = mapped_column(Float, nullable=False)
    quality_status: Mapped[str] = mapped_column(String(40), default="DECLARED", nullable=False)

    order: Mapped[Order] = relationship(back_populates="items")
    listing: Mapped[ProduceListing] = relationship()
    seller: Mapped[User] = relationship()
    crop: Mapped[Crop] = relationship()


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"), nullable=False)
    buyer_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, native_enum=False), default=PaymentStatus.HELD, nullable=False
    )
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    paid_amount: Mapped[float] = mapped_column(Float, nullable=False)
    held_amount: Mapped[float] = mapped_column(Float, nullable=False)
    released_amount: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    remaining_amount: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    label: Mapped[str] = mapped_column(
        String(160), default="Prototype payment protection simulation", nullable=False
    )

    order: Mapped[Order] = relationship()


class PaymentHold(Base, TimestampMixin):
    __tablename__ = "payment_holds"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    payment_id: Mapped[str] = mapped_column(ForeignKey("payments.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[str] = mapped_column(String(160), nullable=False)


class PaymentRelease(Base, TimestampMixin):
    __tablename__ = "payment_releases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    payment_id: Mapped[str] = mapped_column(ForeignKey("payments.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[str] = mapped_column(String(160), nullable=False)


class Vehicle(Base, TimestampMixin):
    __tablename__ = "vehicles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    transporter_id: Mapped[str] = mapped_column(ForeignKey("transporter_profiles.id"), nullable=False)
    registration_number: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    vehicle_type: Mapped[str] = mapped_column(String(80), nullable=False)
    capacity_kg: Mapped[float] = mapped_column(Float, nullable=False)
    cold_chain: Mapped[bool] = mapped_column(default=False, nullable=False)
    document_status: Mapped[str] = mapped_column(String(40), default="VERIFIED", nullable=False)

    transporter: Mapped[TransporterProfile] = relationship(back_populates="vehicles")


class VehicleDocument(Base, TimestampMixin):
    __tablename__ = "vehicle_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    vehicle_id: Mapped[str] = mapped_column(ForeignKey("vehicles.id"), nullable=False)
    document_type: Mapped[str] = mapped_column(String(80), nullable=False)
    file_url: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="VERIFIED", nullable=False)


class RoutePlan(Base, TimestampMixin):
    __tablename__ = "routes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    provider: Mapped[str] = mapped_column(String(80), default="derived-haversine-demo", nullable=False)
    original_distance_km: Mapped[float] = mapped_column(Float, nullable=False)
    optimized_distance_km: Mapped[float] = mapped_column(Float, nullable=False)
    saved_distance_km: Mapped[float] = mapped_column(Float, nullable=False)
    estimated_cost_saving: Mapped[float] = mapped_column(Float, nullable=False)
    route_payload: Mapped[dict[str, Any]] = mapped_column(SAJSON, nullable=False)
    data_classification: Mapped[DataClass] = mapped_column(
        Enum(DataClass, native_enum=False), default=DataClass.DERIVED, nullable=False
    )


class Delivery(Base, TimestampMixin):
    __tablename__ = "deliveries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"), nullable=False)
    transporter_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    vehicle_id: Mapped[str | None] = mapped_column(ForeignKey("vehicles.id"))
    route_id: Mapped[str | None] = mapped_column(ForeignKey("routes.id"))
    status: Mapped[DeliveryStatus] = mapped_column(
        Enum(DeliveryStatus, native_enum=False), default=DeliveryStatus.REQUESTED, nullable=False
    )
    cargo_kg: Mapped[float] = mapped_column(Float, nullable=False)
    estimated_distance_km: Mapped[float] = mapped_column(Float, nullable=False)
    estimated_duration_hours: Mapped[float] = mapped_column(Float, nullable=False)
    estimated_earnings: Mapped[float] = mapped_column(Float, nullable=False)

    order: Mapped[Order] = relationship()
    route: Mapped[RoutePlan | None] = relationship()
    stops: Mapped[list["DeliveryStop"]] = relationship(
        back_populates="delivery", cascade="all, delete-orphan", order_by="DeliveryStop.sequence"
    )


class DeliveryStop(Base, TimestampMixin):
    __tablename__ = "delivery_stops"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    delivery_id: Mapped[str] = mapped_column(ForeignKey("deliveries.id"), nullable=False)
    listing_id: Mapped[str | None] = mapped_column(ForeignKey("produce_listings.id"))
    location_id: Mapped[str] = mapped_column(ForeignKey("locations.id"), nullable=False)
    stop_type: Mapped[str] = mapped_column(String(40), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    planned_quantity_kg: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    actual_quantity_kg: Mapped[float | None] = mapped_column(Float)
    status: Mapped[StopStatus] = mapped_column(
        Enum(StopStatus, native_enum=False), default=StopStatus.PENDING, nullable=False
    )

    delivery: Mapped[Delivery] = relationship(back_populates="stops")
    listing: Mapped[ProduceListing | None] = relationship()
    location: Mapped[Location] = relationship()


class RouteEvent(Base, TimestampMixin):
    __tablename__ = "route_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    delivery_id: Mapped[str] = mapped_column(ForeignKey("deliveries.id"), nullable=False)
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    location_id: Mapped[str | None] = mapped_column(ForeignKey("locations.id"))
    payload: Mapped[dict[str, Any]] = mapped_column(SAJSON, default=dict, nullable=False)


class PickupRecord(Base, TimestampMixin):
    __tablename__ = "pickup_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    delivery_id: Mapped[str] = mapped_column(ForeignKey("deliveries.id"), nullable=False)
    stop_id: Mapped[str] = mapped_column(ForeignKey("delivery_stops.id"), nullable=False)
    transporter_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    expected_quantity_kg: Mapped[float] = mapped_column(Float, nullable=False)
    actual_quantity_kg: Mapped[float] = mapped_column(Float, nullable=False)
    grade: Mapped[str] = mapped_column(String(40), nullable=False)
    photo_url: Mapped[str | None] = mapped_column(String(255))
    weighing_slip_url: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)


class DeliveryRecord(Base, TimestampMixin):
    __tablename__ = "delivery_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    delivery_id: Mapped[str] = mapped_column(ForeignKey("deliveries.id"), nullable=False)
    buyer_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    expected_quantity_kg: Mapped[float] = mapped_column(Float, nullable=False)
    delivered_quantity_kg: Mapped[float] = mapped_column(Float, nullable=False)
    decision: Mapped[str] = mapped_column(String(40), nullable=False)
    digital_signature: Mapped[str] = mapped_column(String(160), nullable=False)
    photo_url: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)


class Incident(Base, TimestampMixin):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    delivery_id: Mapped[str] = mapped_column(ForeignKey("deliveries.id"), nullable=False)
    reported_by_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    incident_type: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="INCIDENT_REPORTED", nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    evidence_urls: Mapped[list[str]] = mapped_column(SAJSON, default=list, nullable=False)


class Dispute(Base, TimestampMixin):
    __tablename__ = "disputes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"), nullable=False)
    delivery_id: Mapped[str | None] = mapped_column(ForeignKey("deliveries.id"))
    opened_by_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    dispute_type: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="UNDER_REVIEW", nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(SAJSON, default=dict, nullable=False)


class Rating(Base, TimestampMixin):
    __tablename__ = "ratings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    from_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    to_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    order_id: Mapped[str | None] = mapped_column(ForeignKey("orders.id"))
    score: Mapped[float] = mapped_column(Float, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)


class ReputationScore(Base, TimestampMixin):
    __tablename__ = "reputation_scores"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    role: Mapped[RoleName] = mapped_column(Enum(RoleName, native_enum=False), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    components: Mapped[dict[str, Any]] = mapped_column(SAJSON, nullable=False)

    user: Mapped[User] = relationship()


class MarketPrice(Base, TimestampMixin):
    __tablename__ = "market_prices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    crop_id: Mapped[str] = mapped_column(ForeignKey("crops.id"), nullable=False)
    state: Mapped[str] = mapped_column(String(120), nullable=False)
    district: Mapped[str] = mapped_column(String(120), nullable=False)
    market: Mapped[str] = mapped_column(String(160), nullable=False)
    variety: Mapped[str] = mapped_column(String(120), default="Other", nullable=False)
    grade: Mapped[str] = mapped_column(String(80), default="FAQ", nullable=False)
    arrival_date: Mapped[date] = mapped_column(Date, nullable=False)
    min_price: Mapped[float] = mapped_column(Float, nullable=False)
    max_price: Mapped[float] = mapped_column(Float, nullable=False)
    modal_price: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(40), default="Rs/Quintal", nullable=False)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    data_classification: Mapped[DataClass] = mapped_column(
        Enum(DataClass, native_enum=False), default=DataClass.SYNTHETIC, nullable=False
    )

    crop: Mapped[Crop] = relationship()


class MarketArrival(Base, TimestampMixin):
    __tablename__ = "market_arrivals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    crop_id: Mapped[str] = mapped_column(ForeignKey("crops.id"), nullable=False)
    market: Mapped[str] = mapped_column(String(160), nullable=False)
    arrival_date: Mapped[date] = mapped_column(Date, nullable=False)
    arrival_quantity_tonnes: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    data_classification: Mapped[DataClass] = mapped_column(
        Enum(DataClass, native_enum=False), default=DataClass.PROXY, nullable=False
    )


class WeatherRecord(Base, TimestampMixin):
    __tablename__ = "weather_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    location_id: Mapped[str] = mapped_column(ForeignKey("locations.id"), nullable=False)
    observed_date: Mapped[date] = mapped_column(Date, nullable=False)
    rainfall_mm: Mapped[float] = mapped_column(Float, nullable=False)
    temperature_c: Mapped[float] = mapped_column(Float, nullable=False)
    humidity_percent: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    data_classification: Mapped[DataClass] = mapped_column(
        Enum(DataClass, native_enum=False), default=DataClass.SOURCE_READY, nullable=False
    )


class PricePrediction(Base, TimestampMixin):
    __tablename__ = "price_predictions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    crop_id: Mapped[str] = mapped_column(ForeignKey("crops.id"), nullable=False)
    market: Mapped[str] = mapped_column(String(160), nullable=False)
    horizon_days: Mapped[int] = mapped_column(Integer, nullable=False)
    predicted_min_price: Mapped[float] = mapped_column(Float, nullable=False)
    predicted_max_price: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    model_name: Mapped[str] = mapped_column(String(120), nullable=False)
    data_classification: Mapped[DataClass] = mapped_column(
        Enum(DataClass, native_enum=False), default=DataClass.DERIVED, nullable=False
    )


class DemandPrediction(Base, TimestampMixin):
    __tablename__ = "demand_predictions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    crop_id: Mapped[str] = mapped_column(ForeignKey("crops.id"), nullable=False)
    region: Mapped[str] = mapped_column(String(160), nullable=False)
    horizon_days: Mapped[int] = mapped_column(Integer, nullable=False)
    demand_level: Mapped[str] = mapped_column(String(40), nullable=False)
    proxy_basis: Mapped[str] = mapped_column(String(160), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    data_classification: Mapped[DataClass] = mapped_column(
        Enum(DataClass, native_enum=False), default=DataClass.PROXY, nullable=False
    )


class Alert(Base, TimestampMixin):
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    crop_id: Mapped[str | None] = mapped_column(ForeignKey("crops.id"))
    alert_type: Mapped[str] = mapped_column(String(80), nullable=False)
    severity: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    data_classification: Mapped[DataClass] = mapped_column(
        Enum(DataClass, native_enum=False), default=DataClass.DERIVED, nullable=False
    )


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    notification_type: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime)


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    actor_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(36))
    old_value: Mapped[dict[str, Any] | None] = mapped_column(SAJSON)
    new_value: Mapped[dict[str, Any] | None] = mapped_column(SAJSON)


class StateRule(Base, TimestampMixin):
    __tablename__ = "state_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    state: Mapped[str] = mapped_column(String(120), nullable=False)
    market_type: Mapped[str] = mapped_column(String(120), nullable=False)
    mandi_requirements: Mapped[str] = mapped_column(Text, nullable=False)
    direct_sale_allowed: Mapped[bool] = mapped_column(default=True, nullable=False)
    documentation_requirements: Mapped[list[str]] = mapped_column(SAJSON, default=list, nullable=False)
    special_rules: Mapped[str] = mapped_column(Text, nullable=False)
    data_classification: Mapped[DataClass] = mapped_column(
        Enum(DataClass, native_enum=False), default=DataClass.SYNTHETIC, nullable=False
    )


class DataSource(Base, TimestampMixin):
    __tablename__ = "data_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    official_source: Mapped[str] = mapped_column(String(180), nullable=False)
    url: Mapped[str] = mapped_column(String(255), nullable=False)
    access_method: Mapped[str] = mapped_column(String(120), nullable=False)
    format: Mapped[str] = mapped_column(String(80), nullable=False)
    fields: Mapped[list[str]] = mapped_column(SAJSON, nullable=False)
    geographic_coverage: Mapped[str] = mapped_column(String(180), nullable=False)
    time_range: Mapped[str] = mapped_column(String(180), nullable=False)
    update_frequency: Mapped[str] = mapped_column(String(120), nullable=False)
    license: Mapped[str] = mapped_column(String(180), nullable=False)
    usable_for_ml: Mapped[bool] = mapped_column(default=True, nullable=False)
    limitations: Mapped[str] = mapped_column(Text, nullable=False)
    data_classification: Mapped[DataClass] = mapped_column(
        Enum(DataClass, native_enum=False), default=DataClass.REAL, nullable=False
    )
