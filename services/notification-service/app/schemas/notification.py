from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class NotificationCreate(BaseModel):
    user_id: Optional[str] = None
    title: str
    message: str
    alert_type: str = "SYSTEM"
    severity: str = "INFO"

class NotificationResponse(BaseModel):
    id: str
    user_id: Optional[str]
    title: str
    message: str
    alert_type: str
    severity: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
