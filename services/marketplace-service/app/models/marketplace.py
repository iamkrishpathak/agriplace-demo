import enum
import uuid
from datetime import date, datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, Enum, JSON, Date, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base

def new_uuid() -> str:
    return str(uuid.uuid4())

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

class Grade(str, enum.Enum):
    A = "Grade A"
    B = "Grade B"
    C = "Grade C"

class DataClass(str, enum.Enum):
    REAL = "REAL"
    SYNTHETIC = "SYNTHETIC"
    DERIVED = "DERIVED"

class Crop(Base):
    __tablename__ = "crops"
    id = Column(String(36), primary_key=True, default=new_uuid)
    name = Column(String(120), unique=True, nullable=False)
    hindi_name = Column(String(120), nullable=False)
    perishability = Column(String(40), default="MEDIUM", nullable=False)

class ProduceListing(Base):
    __tablename__ = "produce_listings"
    id = Column(String(36), primary_key=True, default=new_uuid)
    farmer_id = Column(String(36), nullable=False) # Refers to User Service
    crop_id = Column(String(36), ForeignKey("crops.id"), nullable=False)
    location_id = Column(String(36), nullable=False) # Refers to User Service location
    quantity_kg = Column(Float, nullable=False)
    available_date = Column(Date, nullable=False)
    grade = Column(Enum(Grade, native_enum=False), nullable=False)
    status = Column(Enum(ListingStatus, native_enum=False), default=ListingStatus.ACTIVE, nullable=False)
    expected_price_per_kg = Column(Float, nullable=False)
    image_url = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    crop = relationship("Crop")

class BuyerRequirement(Base):
    __tablename__ = "buyer_requirements"
    id = Column(String(36), primary_key=True, default=new_uuid)
    buyer_id = Column(String(36), nullable=False)
    crop_id = Column(String(36), ForeignKey("crops.id"), nullable=False)
    destination_location_id = Column(String(36), nullable=False)
    required_quantity_kg = Column(Float, nullable=False)
    grade = Column(Enum(Grade, native_enum=False), nullable=False)
    needed_by = Column(Date, nullable=False)
    max_price_per_kg = Column(Float, nullable=False)
    status = Column(Enum(RequirementStatus, native_enum=False), default=RequirementStatus.OPEN, nullable=False)
    recurring = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    crop = relationship("Crop")

class OrderMatch(Base):
    __tablename__ = "order_matches"
    id = Column(String(36), primary_key=True, default=new_uuid)
    requirement_id = Column(String(36), ForeignKey("buyer_requirements.id"), nullable=False)
    listing_id = Column(String(36), ForeignKey("produce_listings.id"), nullable=False)
    quantity_kg = Column(Float, nullable=False)
    score = Column(Float, nullable=False)
    score_breakdown = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
