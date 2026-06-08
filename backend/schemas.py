from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

# --- 1. مخططات المستخدم (User Schemas) ---

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    phone: str
    role: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    phone: Optional[str] = None


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str
    phone: Optional[str] = None
    profile_image: Optional[str] = None

    class Config:
        from_attributes = True


# --- 2. مخططات العقار (Property Schemas) ---

class PropertyCreate(BaseModel):
    title: str
    description: Optional[str] = None
    price: Decimal
    area: float
    bedrooms: int = 0
    bathrooms: int = 0
    property_type: str = "Apartment"
    status: str = "Available"
    address: str = ""
    city: str
    lat: Optional[float] = None
    lng: Optional[float] = None


class PropertyOut(BaseModel):
    id: str
    owner_id: int
    title: str
    description: Optional[str] = None
    price: Decimal
    area: float
    bedrooms: int
    bathrooms: int
    property_type: str
    status: str
    address: Optional[str] = None
    city: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    main_image: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PropertyUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    area: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    property_type: Optional[str] = None
    status: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None


# --- 3. مخططات الحماية (Auth Schemas) ---

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


# --- 4. مخططات الحجوزات (Booking Schemas) ---

class BookingCreate(BaseModel):
    property_id: str
    payment_preference: str = "Full Cash"
    install_years: Optional[int] = None


class BookingOut(BaseModel):
    id: int
    property_id: str
    user_id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# --- 5. مخطط الدردشة (Chat Schema) ---
class ChatRequest(BaseModel):
     message: str