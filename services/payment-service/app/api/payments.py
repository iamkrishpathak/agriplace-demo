from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.security import get_current_user, CurrentUser, require_roles
from app.models.payment import Payment, PaymentHold, PaymentStatus, PaymentHoldStatus
from app.schemas.payment import PaymentCreate, PaymentResponse, HoldCreate, HoldResponse
import uuid

router = APIRouter()

def api_response(data=None, error=None, success=True):
    return {"success": success, "data": data, "error": error}

@router.post("/", response_model=dict)
def create_payment(payload: PaymentCreate, user: CurrentUser = Depends(require_roles(["BUYER"])), db: Session = Depends(get_db)):
    # Mocking actual payment gateway integration
    payment = Payment(
        order_id=payload.order_id,
        payer_id=user.id,
        amount=payload.amount,
        currency=payload.currency,
        payment_method=payload.payment_method,
        status=PaymentStatus.COMPLETED,  # Assume auto-success for demo
        transaction_id=f"TXN-{str(uuid.uuid4())[:12].upper()}"
    )
    db.add(payment)
    db.flush()

    # Create holds for farmer (and transporter if applicable)
    # This logic normally comes from the Order/Logistics service via webhook/sync call
    # We will simulate a simple 95% hold for seller
    hold = PaymentHold(
        payment_id=payment.id,
        payee_id="SELLER_PLACEHOLDER", # Should be passed dynamically
        amount=payload.amount * 0.95,
        reason="ESCROW_FARMER_PAYOUT"
    )
    db.add(hold)

    db.commit()
    db.refresh(payment)
    return api_response(PaymentResponse.model_validate(payment).model_dump())

@router.get("/", response_model=dict)
def get_payments(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    payments = db.query(Payment).filter(Payment.payer_id == user.id).all()
    return api_response([PaymentResponse.model_validate(p).model_dump() for p in payments])

@router.post("/{payment_id}/release", response_model=dict)
def release_payment(payment_id: str, db: Session = Depends(get_db)):
    # In a real app this would be triggered internally after delivery confirmation
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    for hold in payment.holds:
        if hold.status == PaymentHoldStatus.HELD:
            hold.status = PaymentHoldStatus.RELEASED
            # trigger actual payout
    
    db.commit()
    return api_response({"message": "Funds released"})
