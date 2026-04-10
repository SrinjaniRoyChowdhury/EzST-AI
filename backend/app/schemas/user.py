"""
schemas/user.py
───────────────
Pydantic schemas for user / business registration.
"""

from pydantic import BaseModel, EmailStr
from app.models.user import UserRole


class BusinessRegisterRequest(BaseModel):
    gstin: str
    legal_name: str
    trade_name: str
    address: str
    state: str
    pin_code: str
    contact_email: EmailStr
    contact_phone: str


class UserProfileResponse(BaseModel):
    id: str
    email: str
    role: UserRole
    full_name: str | None
    business_id: str | None
    is_active: bool