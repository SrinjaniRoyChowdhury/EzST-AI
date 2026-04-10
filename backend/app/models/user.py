"""
models/user.py
──────────────
User and business entity domain models.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4


class UserRole(str, Enum):
    SELLER = "seller"
    BUYER  = "buyer"
    BOTH   = "both"       # Common for GST-registered businesses
    ADMIN  = "admin"


@dataclass
class Business:
    gstin: str            # 15-char GST Identification Number
    legal_name: str
    trade_name: str
    address: str
    state: str
    pin_code: str
    contact_email: str
    contact_phone: str
    id: str = field(default_factory=lambda: str(uuid4()))
    is_verified: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class User:
    email: str
    role: UserRole
    business_id: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid4()))
    full_name: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)