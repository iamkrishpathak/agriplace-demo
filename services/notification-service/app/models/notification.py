import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime

from app.database import Base

def new_uuid() -> str:
    return str(uuid.uuid4())

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(String(36), primary_key=True, default=new_uuid)
    user_id = Column(String(36), nullable=True) # None means broadcast
    title = Column(String(200), nullable=False)
    message = Column(String(1000), nullable=False)
    alert_type = Column(String(80), nullable=False)
    severity = Column(String(40), nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
