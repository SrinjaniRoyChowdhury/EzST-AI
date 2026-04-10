"""
api/routes/auth_routes.py
Auth endpoints – thin wrappers around Supabase Auth.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from typing import Annotated
from datetime import datetime
import uuid

from app.db.supabase_client import get_supabase, db_insert, db_select, db_update
from app.core.security import get_current_user
from app.schemas.user import BusinessRegisterRequest, UserProfileResponse
from app.graph.graph_queries import upsert_business

router = APIRouter(prefix="/auth", tags=["Auth"])

CurrentUser = Annotated[dict, Depends(get_current_user)]

# ─────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────

class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "seller"   # "seller" | "buyer" | "both"


class SignInRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str


# ─────────────────────────────────────────────────────────────
# Sign Up
# ─────────────────────────────────────────────────────────────

@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def sign_up(payload: SignUpRequest):
    supabase = get_supabase()

    try:
        resp = supabase.auth.sign_up({
            "email": payload.email,
            "password": payload.password,
            "options": {
                "data": {
                    "full_name": payload.full_name,
                    "role": payload.role,
                }
            },
        })
    except Exception as e:
        if "already registered" in str(e).lower():
            raise HTTPException(status_code=409, detail="Email already registered")
        raise HTTPException(status_code=400, detail=str(e))

    if not resp.user:
        raise HTTPException(status_code=400, detail="Sign-up failed")

    user_id = resp.user.id

    # ✅ Create profile immediately (consistent table name)
    await db_insert("user_profiles", {
        "id": user_id,
        "email": payload.email,
        "full_name": payload.full_name,
        "role": payload.role,
        "is_active": True,
        "created_at": datetime.utcnow().isoformat(),
    })

    return AuthResponse(
        access_token=resp.session.access_token if resp.session else "",
        user_id=user_id,
        email=payload.email,
    )


# ─────────────────────────────────────────────────────────────
# Sign In
# ─────────────────────────────────────────────────────────────

@router.post("/signin", response_model=AuthResponse)
async def sign_in(payload: SignInRequest):
    supabase = get_supabase()

    try:
        resp = supabase.auth.sign_in_with_password({
            "email": payload.email,
            "password": payload.password,
        })
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not resp.session or not resp.user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return AuthResponse(
        access_token=resp.session.access_token,
        user_id=resp.user.id,
        email=resp.user.email,
    )


# ─────────────────────────────────────────────────────────────
# Sign Out
# ─────────────────────────────────────────────────────────────

@router.post("/signout")
async def sign_out(current_user: CurrentUser):
    supabase = get_supabase()

    try:
        supabase.auth.sign_out()
    except Exception:
        raise HTTPException(status_code=400, detail="Sign out failed")

    return {"message": "Signed out successfully"}


# ─────────────────────────────────────────────────────────────
# Get Profile
# ─────────────────────────────────────────────────────────────

@router.get("/me", response_model=UserProfileResponse)
async def get_profile(current_user: CurrentUser):
    user_id = current_user["sub"]

    profiles = await db_select("user_profiles", {"id": user_id})

    if not profiles:
        raise HTTPException(status_code=404, detail="Profile not found")

    p = profiles[0]

    return UserProfileResponse(
        id=p["id"],
        email=p["email"],
        full_name=p.get("full_name"),
        role=p.get("role"),
        business_id=p.get("business_id"),
        is_active=p.get("is_active", True),
    )


# ─────────────────────────────────────────────────────────────
# Register Business
# ─────────────────────────────────────────────────────────────

@router.post("/register-business", status_code=status.HTTP_201_CREATED)
async def register_business(
    payload: BusinessRegisterRequest,
    current_user: CurrentUser,
):
    user_id = current_user["sub"]

    # Check existing GSTIN
    existing = await db_select("businesses", {"gstin": payload.gstin})
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"GSTIN {payload.gstin} already registered"
        )

    business_id = str(uuid.uuid4())

    # Insert business
    await db_insert("businesses", {
        "id": business_id,
        "gstin": payload.gstin,
        "legal_name": payload.legal_name,
        "trade_name": payload.trade_name,
        "address": payload.address,
        "state": payload.state,
        "pin_code": payload.pin_code,
        "contact_email": payload.contact_email,
        "contact_phone": payload.contact_phone,
        "created_at": datetime.utcnow().isoformat(),
    })

    # Link user → business
    await db_update(
        "user_profiles",
        {"id": user_id},
        {"business_id": business_id}
    )

    # Graph DB (Neo4j)
    await upsert_business(
        payload.gstin,
        payload.legal_name,
        payload.state
    )

    return {
        "message": "Business registered successfully",
        "business_id": business_id
    }