"""
User models for SARAI authentication
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime, timezone
import uuid
import re


class UserRole:
    """User role constants"""
    ADMIN = "admin"
    STAFF = "staff"
    VIEWER = "viewer"
    
    @classmethod
    def all_roles(cls):
        return [cls.ADMIN, cls.STAFF, cls.VIEWER]


class User(BaseModel):
    """User database model"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str  # Changed from EmailStr to allow .local domains
    password_hash: str
    name: str
    role: str = UserRole.STAFF  # Default role
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_login: Optional[str] = None
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format (allows .local for development)"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v) and not v.endswith('.local'):
            raise ValueError('Invalid email format')
        return v.lower()


class UserCreate(BaseModel):
    """Schema for creating a new user"""
    email: str
    password: str = Field(min_length=8, description="Minimum 8 characters")
    name: str = Field(min_length=2)
    role: str = UserRole.STAFF
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format (allows .local for development)"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v) and not v.endswith('.local'):
            raise ValueError('Invalid email format')
        return v.lower()
    
    def validate_role(self):
        if self.role not in UserRole.all_roles():
            raise ValueError(f"Invalid role. Must be one of: {', '.join(UserRole.all_roles())}")


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8)


class UserLogin(BaseModel):
    """Schema for user login"""
    email: str
    password: str
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format (allows .local for development)"""
        return v.lower()


class UserResponse(BaseModel):
    """Safe user response (no password_hash)"""
    id: str
    email: str
    name: str
    role: str
    is_active: bool
    created_at: str
    last_login: Optional[str] = None


class LoginResponse(BaseModel):
    """Response for successful login"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
