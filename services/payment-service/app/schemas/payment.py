from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class PaymentCreate(BaseModel):
    order_id: str
    amount: float
    currency: str = "INR"
    payment_method: str

class PaymentResponse(BaseModel):
    id: str
    order_id: str
    payer_id: str
    amount: float
    currency: str
    status: str
    payment_method: Optional[str]
    transaction_id: Optional[str]

    class Config:
        from_attributes = True

class HoldCreate(BaseModel):
    payee_id: str
    amount: float
    reason: str

class HoldResponse(BaseModel):
    id: str
    payment_id: str
    payee_id: str
    amount: float
    reason: str
    status: str

    class Config:
        from_attributes = True
