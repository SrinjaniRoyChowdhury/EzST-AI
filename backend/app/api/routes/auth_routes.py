"""
api/routes/auth_routes.py
──────────────────────────
Auth endpoints – thin wrappers around Supabase Auth.
Supabase handles password hashing, JWT issuance, and refresh tokens.
These routes expose Supabase auth to our API consumers.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from typing import Annotated

from app.db.supabase_client import get_supabase
from app.core.security import get_current_user
from app.schemas.user import BusinessRegisterRequest, UserProfileResponse
from app.db.supabase_client import db_insert, db_select
from app.graph.graph_queries import upsert_business

router = APIRouter(prefix="/auth", tags=["Auth"])
CurrentUser = Annotated[dict, Depends(get_current_user)]


# ── Request / Response schemas (auth-specific) ───────────────

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


# ── Sign Up ───────────────────────────────────────────────────

@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def sign_up(payload: SignUpRequest):
    """
    Register a new user via Supabase Auth.
    Creates the auth user and a corresponding profile record.
    """
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if not resp.user:
        raise HTTPException(status_code=400, detail="Sign-up failed. Check your email.")

    # Create user profile in our custom table
    await db_insert("user_profiles", {
        "id": resp.user.id,
        "email": payload.email,
        "full_name": payload.full_name,
        "role": payload.role,
        "is_active": True,
    })

    return AuthResponse(
        access_token=resp.session.access_token if resp.session else "",
        user_id=resp.user.id,
        email=resp.user.email,
    )


# ── Sign In ───────────────────────────────────────────────────

@router.post("/signin", response_model=AuthResponse)
async def sign_in(payload: SignInRequest):
    """Sign in with email/password. Returns Supabase JWT."""
    supabase = get_supabase()
    try:
        resp = supabase.auth.sign_in_with_password({
            "email": payload.email,
            "password": payload.password,
        })
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    if not resp.session:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return AuthResponse(
        access_token=resp.session.access_token,
        user_id=resp.user.id,
        email=resp.user.email,
    )


# ── Sign Out ──────────────────────────────────────────────────

@router.post("/signout")
async def sign_out(current_user: CurrentUser = None):
    """Invalidate the current session."""
    supabase = get_supabase()
    supabase.auth.sign_out()
    return {"message": "Signed out successfully"}


# ── Profile ───────────────────────────────────────────────────

@router.get("/me", response_model=UserProfileResponse)
async def get_profile(current_user: CurrentUser = None):
    """Return the current user's profile."""
    user_id = current_user["sub"]
    profiles = await db_select("user_profiles", {"id": user_id})
    if not profiles:
        raise HTTPException(status_code=404, detail="Profile not found")
    p = profiles[0]
    return UserProfileResponse(
        id=p["id"],
        email=p["email"],
        role=p["role"],
        full_name=p.get("full_name"),
        business_id=p.get("business_id"),
        is_active=p.get("is_active", True),
    )


# ── Business Registration ─────────────────────────────────────

@router.post("/register-business", status_code=status.HTTP_201_CREATED)
async def register_business(
    payload: BusinessRegisterRequest,
    current_user: CurrentUser = None,
):
    """
    Register a GST business and link it to the current user.
    Also creates/updates the Business node in Neo4j.
    """
    import uuid
    from datetime import datetime

    user_id = current_user["sub"]
    business_id = str(uuid.uuid4())

    # Validate GSTIN uniqueness
    existing = await db_select("businesses", {"gstin": payload.gstin})
    if existing:
        raise HTTPException(status_code=409, detail=f"GSTIN {payload.gstin} already registered")

    # Store in Supabase
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

    # Link user to business
    from app.db.supabase_client import db_update
    await db_update("user_profiles", {"id": user_id}, {"business_id": business_id})

    # Upsert in Neo4j graph
    await upsert_business(payload.gstin, payload.legal_name, payload.state)

    return {"message": "Business registered successfully", "business_id": business_id}