import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Enum, JSON, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from app.database import Base

def new_uuid() -> str:
    return str(uuid.uuid4())

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

class Delivery(Base):
    __tablename__ = "deliveries"
    id = Column(String(36), primary_key=True, default=new_uuid)
    order_id = Column(String(36), nullable=False)
    transporter_id = Column(String(36))
    vehicle_id = Column(String(36))
    route_id = Column(String(36))
    status = Column(Enum(DeliveryStatus, native_enum=False), default=DeliveryStatus.REQUESTED, nullable=False)
    cargo_kg = Column(Float, nullable=False)
    estimated_distance_km = Column(Float, nullable=False)
    estimated_duration_hours = Column(Float, nullable=False)
    estimated_earnings = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    stops = relationship("DeliveryStop", back_populates="delivery", cascade="all, delete-orphan")

class DeliveryStop(Base):
    __tablename__ = "delivery_stops"
    id = Column(String(36), primary_key=True, default=new_uuid)
    delivery_id = Column(String(36), ForeignKey("deliveries.id"), nullable=False)
    location_id = Column(String(36), nullable=False)
    stop_type = Column(String(40), nullable=False) # PICKUP or DROPOFF
    sequence = Column(Integer, nullable=False)
    planned_quantity_kg = Column(Float, default=0, nullable=False)
    actual_quantity_kg = Column(Float)
    status = Column(Enum(StopStatus, native_enum=False), default=StopStatus.PENDING, nullable=False)

    delivery = relationship("Delivery", back_populates="stops")

class Incident(Base):
    __tablename__ = "incidents"
    id = Column(String(36), primary_key=True, default=new_uuid)
    delivery_id = Column(String(36), ForeignKey("deliveries.id"), nullable=False)
    reported_by_id = Column(String(36), nullable=False)
    incident_type = Column(String(80), nullable=False)
    status = Column(String(40), default="INCIDENT_REPORTED", nullable=False)
    description = Column(Text, nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)
    evidence_urls = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
