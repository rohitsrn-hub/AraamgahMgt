"""
Authentication utilities for SARAI
Handles JWT token creation/verification and password hashing
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
import os
from functools import wraps

# Password hashing context (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "CHANGE_THIS_IN_PRODUCTION_USE_openssl_rand_hex_32")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.environ.get("JWT_EXPIRE_MINUTES", "1440"))  # 24 hours

# HTTP Bearer token scheme
security = HTTPBearer()


# ============= PASSWORD HASHING =============

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    Generates a new salt for each password (DO NOT store salt in .env).
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    """
    return pwd_context.verify(plain_password, hashed_password)


# ============= JWT TOKEN MANAGEMENT =============

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Payload to encode (must include user_id and role)
        expires_delta: Custom expiration time (optional)
    
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    })
    
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Dict:
    """
    Decode and verify a JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded payload dict
    
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid authentication token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ============= DEPENDENCIES FOR ROUTE PROTECTION =============

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db = None  # Will be injected via closure
) -> Dict:
    """
    Dependency to extract and verify current user from JWT token.
    
    Usage:
        @app.get("/protected")
        async def protected_route(current_user = Depends(get_current_user)):
            return {"user": current_user}
    
    Returns:
        User dict from database
    
    Raises:
        HTTPException 401: If token is invalid or user not found
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get database instance (will be passed from server.py)
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    # Fetch user from database
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=403,
            detail="User account is disabled",
        )
    
    return user


# ============= ROLE-BASED ACCESS CONTROL =============

class UserRole:
    """User role constants"""
    ADMIN = "admin"
    STAFF = "staff"
    VIEWER = "viewer"


def require_role(allowed_roles: list):
    """
    Decorator to require specific roles for a route.
    
    Usage:
        @app.get("/admin-only")
        @require_role([UserRole.ADMIN])
        async def admin_route(current_user = Depends(get_current_user)):
            return {"message": "Admin access granted"}
    """
    def decorator(current_user: Dict):
        user_role = current_user.get("role")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}",
            )
        return current_user
    return decorator


def require_admin(current_user: Dict = Depends(get_current_user)) -> Dict:
    """
    Dependency to require admin role.
    
    Usage:
        @app.get("/admin")
        async def admin_route(current_user = Depends(require_admin)):
            return {"message": "Admin only"}
    """
    return require_role([UserRole.ADMIN])(current_user)


def require_staff_or_admin(current_user: Dict = Depends(get_current_user)) -> Dict:
    """
    Dependency to require staff or admin role.
    
    Usage:
        @app.get("/bookings")
        async def bookings_route(current_user = Depends(require_staff_or_admin)):
            return {"bookings": [...]}
    """
    return require_role([UserRole.ADMIN, UserRole.STAFF])(current_user)


# ============= HELPER FUNCTIONS =============

def create_user_response(user: Dict) -> Dict:
    """
    Create a safe user response (exclude password_hash).
    
    Args:
        user: User dict from database
    
    Returns:
        Safe user dict for API response
    """
    safe_user = {
        "id": user.get("id"),
        "email": user.get("email"),
        "name": user.get("name"),
        "role": user.get("role"),
        "is_active": user.get("is_active", True),
        "created_at": user.get("created_at"),
        "last_login": user.get("last_login"),
    }
    return safe_user
