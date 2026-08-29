import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base

def new_uuid() -> str:
    return str(uuid.uuid4())

class OrderStatus(str, enum.Enum):
    CREATED = "CREATED"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PAYMENT_SECURED = "PAYMENT_SECURED"
    QUALITY_VERIFICATION = "QUALITY_VERIFICATION"
    TRANSPORT_PENDING = "TRANSPORT_PENDING"
    TRANSPORT_ASSIGNED = "TRANSPORT_ASSIGNED"
    PICKED_UP = "PICKED_UP"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    SETTLEMENT_PENDING = "SETTLEMENT_PENDING"
    COMPLETED = "COMPLETED"
    DISPUTED = "DISPUTED"
    CANCELLED = "CANCELLED"

class Order(Base):
    __tablename__ = "orders"
    id = Column(String(36), primary_key=True, default=new_uuid)
    order_number = Column(String(40), unique=True, nullable=False)
    buyer_id = Column(String(36), nullable=False)
    requirement_id = Column(String(36)) # nullable, could be direct order
    status = Column(Enum(OrderStatus, native_enum=False), default=OrderStatus.CREATED, nullable=False)
    total_quantity_kg = Column(Float, nullable=False)
    total_value = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(String(36), primary_key=True, default=new_uuid)
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=False)
    listing_id = Column(String(36), nullable=False)
    seller_id = Column(String(36), nullable=False)
    crop_id = Column(String(36), nullable=False)
    quantity_kg = Column(Float, nullable=False)
    price_per_kg = Column(Float, nullable=False)
    quality_status = Column(String(40), default="DECLARED", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    order = relationship("Order", back_populates="items")
