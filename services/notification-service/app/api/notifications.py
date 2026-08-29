from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.core.security import get_current_user, CurrentUser
from app.models.notification import Notification
from app.schemas.notification import NotificationCreate, NotificationResponse

router = APIRouter()

def api_response(data=None, error=None, success=True):
    return {"success": success, "data": data, "error": error}

@router.post("/", response_model=dict)
def create_notification(payload: NotificationCreate, db: Session = Depends(get_db)):
    # In a real microservice architecture, this endpoint would be called internally by other services.
    # It would ideally be protected by a service-to-service auth mechanism.
    notification = Notification(
        user_id=payload.user_id,
        title=payload.title,
        message=payload.message,
        alert_type=payload.alert_type,
        severity=payload.severity
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return api_response(NotificationResponse.model_validate(notification).model_dump())

@router.get("/", response_model=dict)
def get_notifications(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    notifications = db.query(Notification).filter(
        or_(Notification.user_id == user.id, Notification.user_id == None)
    ).order_by(Notification.created_at.desc()).limit(50).all()
    return api_response([NotificationResponse.model_validate(n).model_dump() for n in notifications])

@router.post("/{notification_id}/read", response_model=dict)
def mark_read(notification_id: str, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    if notification.user_id and notification.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not permitted")
    
    notification.is_read = True
    db.commit()
    return api_response({"message": "Marked as read"})
