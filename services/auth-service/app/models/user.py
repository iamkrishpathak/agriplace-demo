import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

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

class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, default=new_uuid)
    name = Column(String(160), nullable=False)
    phone = Column(String(24), unique=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    preferred_language = Column(String(8), default="en", nullable=False)
    status = Column(Enum(UserStatus, native_enum=False), default=UserStatus.VERIFIED, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    roles = relationship("Role", back_populates="user", cascade="all, delete-orphan")

class Role(Base):
    __tablename__ = "roles"
    id = Column(String(36), primary_key=True, default=new_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    name = Column(Enum(RoleName, native_enum=False), nullable=False)

    user = relationship("User", back_populates="roles")
