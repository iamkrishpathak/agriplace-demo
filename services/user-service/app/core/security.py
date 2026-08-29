from jose import jwt, JWTError
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
from pydantic import BaseModel

security = HTTPBearer(auto_error=False)

class CurrentUser(BaseModel):
    id: str
    roles: list[str]

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> CurrentUser:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        return CurrentUser(id=payload.get("sub"), roles=payload.get("roles", []))
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def require_roles(allowed_roles: list[str]):
    def _dependency(user: CurrentUser = Depends(get_current_user)):
        if not any(role in allowed_roles for role in user.roles):
            raise HTTPException(status_code=403, detail="Role not permitted")
        return user
    return _dependency
