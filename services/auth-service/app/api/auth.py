from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, Role, RoleName
from app.schemas.user import RegisterRequest, LoginRequest, RefreshRequest, TokenResponse, UserResponse
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
from app.core.config import settings

router = APIRouter()
security = HTTPBearer(auto_error=False)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        payload = decode_token(credentials.credentials)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token")
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")
    
    user = db.query(User).filter(User.id == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def api_response(data=None, error=None, success=True):
    return {"success": success, "data": data, "error": error}

@router.post("/register")
async def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if payload.role == RoleName.ADMIN:
        raise HTTPException(status_code=403, detail="Admin registration is not allowed publicly")

    if payload.email:
        existing = db.query(User).filter(User.email == payload.email).first()
        if existing:
            raise HTTPException(status_code=409, detail="Email already registered")
    
    if payload.phone:
        existing = db.query(User).filter(User.phone == payload.phone).first()
        if existing:
            raise HTTPException(status_code=409, detail="Phone already registered")

    if not payload.email and not payload.phone:
        raise HTTPException(status_code=400, detail="Either email or phone is required")

    user = User(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        preferred_language=payload.preferred_language,
    )
    db.add(user)
    db.flush()
    db.add(Role(user_id=user.id, name=payload.role))
    db.commit()
    db.refresh(user)

    # Note: In a complete system, we would notify the User Service here to create FarmerProfile etc.
    # For now, Auth service successfully created the identity.

    return api_response({"user_id": user.id, "role": payload.role.value})

@router.post("/login", response_model=dict)
async def login(payload: LoginRequest, db: Session = Depends(get_db)):
    if not payload.email and not payload.phone:
        raise HTTPException(status_code=400, detail="Either email or phone is required")

    user = None
    if payload.email:
        user = db.query(User).filter(User.email == payload.email).first()
    elif payload.phone:
        user = db.query(User).filter(User.phone == payload.phone).first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    roles = [r.name.value for r in user.roles]
    access_token = create_access_token(user.id, roles)
    refresh_token = create_refresh_token(user.id)

    return api_response({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "roles": roles,
            "status": user.status.value,
            "preferred_language": user.preferred_language
        }
    })

@router.post("/refresh")
async def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    try:
        token_data = decode_token(payload.refresh_token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if token_data.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    user = db.query(User).filter(User.id == token_data.get("sub")).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    roles = [r.name.value for r in user.roles]
    access_token = create_access_token(user.id, roles)
    refresh_token = create_refresh_token(user.id)

    return api_response({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    })

@router.post("/logout")
async def logout():
    # In a stateless JWT implementation, logout is handled client-side.
    # Optionally, we could add token blacklisting here.
    return api_response({"message": "Successfully logged out"})

@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    roles = [r.name.value for r in user.roles]
    return api_response({
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "roles": roles,
        "status": user.status.value,
        "preferred_language": user.preferred_language
    })
