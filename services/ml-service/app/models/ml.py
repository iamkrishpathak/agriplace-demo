import enum
import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, Float, DateTime, Enum, JSON, Integer, Date

from app.database import Base

def new_uuid() -> str:
    return str(uuid.uuid4())

class DemandPrediction(Base):
    __tablename__ = "demand_predictions"
    id = Column(String(36), primary_key=True, default=new_uuid)
    crop_id = Column(String(36), nullable=False)
    region = Column(String(80), nullable=False)
    horizon_days = Column(Integer, nullable=False)
    demand_level = Column(String(40), nullable=False)
    confidence = Column(Float, nullable=False)
    proxy_basis = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class RoutePlan(Base):
    __tablename__ = "route_plans"
    id = Column(String(36), primary_key=True, default=new_uuid)
    vehicle_id = Column(String(36), nullable=False)
    total_distance_km = Column(Float, nullable=False)
    stops_sequence = Column(JSON, nullable=False) # list of location_ids in order
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
