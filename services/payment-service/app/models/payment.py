import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base

def new_uuid() -> str:
    return str(uuid.uuid4())

class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"

class PaymentHoldStatus(str, enum.Enum):
    HELD = "HELD"
    RELEASED = "RELEASED"
    DISPUTED = "DISPUTED"

class Payment(Base):
    __tablename__ = "payments"
    id = Column(String(36), primary_key=True, default=new_uuid)
    order_id = Column(String(36), nullable=False)
    payer_id = Column(String(36), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="INR", nullable=False)
    status = Column(Enum(PaymentStatus, native_enum=False), default=PaymentStatus.PENDING, nullable=False)
    payment_method = Column(String(80))
    transaction_id = Column(String(120), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    holds = relationship("PaymentHold", back_populates="payment", cascade="all, delete-orphan")

class PaymentHold(Base):
    __tablename__ = "payment_holds"
    id = Column(String(36), primary_key=True, default=new_uuid)
    payment_id = Column(String(36), ForeignKey("payments.id"), nullable=False)
    payee_id = Column(String(36), nullable=False)
    amount = Column(Float, nullable=False)
    reason = Column(String(80), nullable=False)
    status = Column(Enum(PaymentHoldStatus, native_enum=False), default=PaymentHoldStatus.HELD, nullable=False)
    release_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    payment = relationship("Payment", back_populates="holds")
