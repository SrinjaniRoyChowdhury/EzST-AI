"""
db/supabase_client.py
─────────────────────
Initialises the Supabase Python client.
Use `get_supabase()` for normal queries (anon key).
Use `get_supabase_admin()` for service-role operations (bypass RLS).
"""

from functools import lru_cache
from supabase import create_client, Client
from app.core.config import get_settings

settings = get_settings()


@lru_cache
def get_supabase() -> Client:
    """Public-facing client – respects Row Level Security."""
    return create_client(settings.supabase_url, settings.supabase_key)


@lru_cache
def get_supabase_admin() -> Client:
    """
    Service-role client – bypasses RLS.
    ONLY use server-side; never expose this key to the frontend.
    """
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


# ── Convenience helpers ──────────────────────────────────────

async def db_insert(table: str, data: dict) -> dict:
    client = get_supabase_admin()
    response = client.table(table).insert(data).execute()
    return response.data[0] if response.data else {}


async def db_select(table: str, filters: dict | None = None) -> list[dict]:
    client = get_supabase_admin()
    query = client.table(table).select("*")
    if filters:
        for key, value in filters.items():
            query = query.eq(key, value)
    response = query.execute()
    return response.data or []


async def db_update(table: str, match: dict, data: dict) -> dict:
    client = get_supabase_admin()
    query = client.table(table).update(data)
    for key, value in match.items():
        query = query.eq(key, value)
    response = query.execute()
    return response.data[0] if response.data else {}


async def db_delete(table: str, match: dict) -> bool:
    client = get_supabase_admin()
    query = client.table(table).delete()
    for key, value in match.items():
        query = query.eq(key, value)
    response = query.execute()
    return bool(response.data)