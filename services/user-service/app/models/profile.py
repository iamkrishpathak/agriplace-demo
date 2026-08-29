import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, Enum, JSON
from sqlalchemy.ext.declarative import declarative_base

from app.database import Base

def new_uuid() -> str:
    return str(uuid.uuid4())

class DataClass(str, enum.Enum):
    REAL = "REAL"
    SYNTHETIC = "SYNTHETIC"
    DERIVED = "DERIVED"
    PROXY = "PROXY"
    SOURCE_READY = "SOURCE_READY"

class Location(Base):
    __tablename__ = "locations"
    id = Column(String(36), primary_key=True, default=new_uuid)
    user_id = Column(String(36), index=True) # Used to link a location to a user/profile
    label = Column(String(160), nullable=False)
    address = Column(String(500), nullable=False)
    district = Column(String(120), nullable=False)
    state = Column(String(120), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location_type = Column(String(80), nullable=False)
    data_classification = Column(Enum(DataClass, native_enum=False), default=DataClass.SYNTHETIC, nullable=False)

class FarmerProfile(Base):
    __tablename__ = "farmer_profiles"
    id = Column(String(36), primary_key=True, default=new_uuid)
    user_id = Column(String(36), unique=True, nullable=False)
    village = Column(String(120), nullable=False)
    district = Column(String(120), nullable=False)
    state = Column(String(120), nullable=False)
    land_acres = Column(Float, default=2.0, nullable=False)
    fpo_id = Column(String(36))
    verification_status = Column(String(32), default="VERIFIED", nullable=False)

class BuyerProfile(Base):
    __tablename__ = "buyer_profiles"
    id = Column(String(36), primary_key=True, default=new_uuid)
    user_id = Column(String(36), unique=True, nullable=False)
    buyer_type = Column(String(80), nullable=False)
    business_name = Column(String(160), nullable=False)
    gstin = Column(String(32))
    verification_status = Column(String(32), default="VERIFIED", nullable=False)

class TransporterProfile(Base):
    __tablename__ = "transporter_profiles"
    id = Column(String(36), primary_key=True, default=new_uuid)
    user_id = Column(String(36), unique=True, nullable=False)
    company_name = Column(String(160), nullable=False)
    license_number = Column(String(80), nullable=False)
    verification_status = Column(String(32), default="VERIFIED", nullable=False)

class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(String(36), primary_key=True, default=new_uuid)
    transporter_id = Column(String(36), nullable=False)
    registration_number = Column(String(40), unique=True, nullable=False)
    vehicle_type = Column(String(80), nullable=False)
    capacity_kg = Column(Float, nullable=False)
    cold_chain = Column(Boolean, default=False, nullable=False)
    document_status = Column(String(40), default="VERIFIED", nullable=False)
