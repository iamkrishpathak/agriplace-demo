from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.security import get_current_user, CurrentUser, require_roles
from app.models.order import Order, OrderItem, OrderStatus
from app.schemas.order import OrderCreate, OrderResponse
import httpx
from app.core.config import settings
import uuid

router = APIRouter()

def api_response(data=None, error=None, success=True):
    return {"success": success, "data": data, "error": error}

async def fetch_listing_details(listing_id: str):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{settings.marketplace_service_url}/api/v1/marketplace/internal/listings/{listing_id}")
            if resp.status_code == 200:
                return resp.json()["data"]
        except Exception:
            pass
    return None

@router.post("/", response_model=dict)
async def create_order(payload: OrderCreate, user: CurrentUser = Depends(require_roles(["BUYER"])), db: Session = Depends(get_db)):
    if not payload.items:
        raise HTTPException(status_code=400, detail="Order must contain items")

    order = Order(
        order_number=f"ORD-{str(uuid.uuid4())[:8].upper()}",
        buyer_id=user.id,
        requirement_id=payload.requirement_id,
        total_quantity_kg=0,
        total_value=0
    )
    db.add(order)
    db.flush()

    total_kg = 0
    total_val = 0

    for item in payload.items:
        listing = await fetch_listing_details(item.listing_id)
        if not listing:
            raise HTTPException(status_code=400, detail=f"Listing {item.listing_id} not found")
        
        # Verify sufficient quantity
        if listing["quantity_kg"] < item.quantity_kg:
            raise HTTPException(status_code=400, detail=f"Insufficient inventory for listing {item.listing_id}")
        
        order_item = OrderItem(
            order_id=order.id,
            listing_id=listing["id"],
            seller_id=listing["farmer_id"],
            crop_id=listing["crop_id"],
            quantity_kg=item.quantity_kg,
            price_per_kg=listing["expected_price_per_kg"]
        )
        db.add(order_item)
        total_kg += item.quantity_kg
        total_val += (item.quantity_kg * listing["expected_price_per_kg"])

    order.total_quantity_kg = total_kg
    order.total_value = total_val
    order.status = OrderStatus.PAYMENT_PENDING
    
    # Ideally, trigger PaymentService here via HTTP to create a Payment intent
    
    db.commit()
    db.refresh(order)
    return api_response(OrderResponse.model_validate(order).model_dump())

@router.get("/", response_model=dict)
def get_orders(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    if "BUYER" in user.roles:
        orders = db.query(Order).filter(Order.buyer_id == user.id).all()
    elif "FARMER" in user.roles:
        # Complex query to find orders containing items from this farmer
        orders = db.query(Order).join(OrderItem).filter(OrderItem.seller_id == user.id).all()
    else:
        orders = db.query(Order).all()
        
    return api_response([OrderResponse.model_validate(o).model_dump() for o in orders])

@router.get("/{order_id}", response_model=dict)
def get_order(order_id: str, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return api_response(OrderResponse.model_validate(order).model_dump())
