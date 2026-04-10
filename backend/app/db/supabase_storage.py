"""
db/supabase_storage.py
───────────────────────
Supabase Storage helpers for invoice PDF/image uploads.

Bucket: "invoices"
Path convention: invoices/{seller_id}/{invoice_id}_{filename}

Create the bucket once in the Supabase dashboard:
  Storage → New Bucket → name: "invoices" → Private
"""

import mimetypes
from pathlib import Path

from app.db.supabase_client import get_supabase_admin
from app.core.config import get_settings

settings = get_settings()

BUCKET = "invoices"


def upload_invoice_file(
    file_bytes: bytes,
    filename: str,
    seller_id: str,
    invoice_id: str,
) -> str:
    """
    Upload invoice bytes to Supabase Storage.

    Returns the public-accessible path (storage path, not a URL).
    Use `get_signed_url` to generate a time-limited download link.
    """
    suffix = Path(filename).suffix.lower()
    content_type = mimetypes.types_map.get(suffix, "application/octet-stream")

    storage_path = f"{seller_id}/{invoice_id}{suffix}"

    client = get_supabase_admin()
    client.storage.from_(BUCKET).upload(
        path=storage_path,
        file=file_bytes,
        file_options={"content-type": content_type, "upsert": "true"},
    )
    return storage_path


def get_signed_url(storage_path: str, expires_in: int = 3600) -> str:
    """
    Generate a short-lived signed URL for downloading an invoice file.

    Args:
        storage_path: The path returned by upload_invoice_file().
        expires_in:   Seconds until the URL expires (default 1 hour).

    Returns:
        A signed download URL string.
    """
    client = get_supabase_admin()
    response = client.storage.from_(BUCKET).create_signed_url(
        storage_path, expires_in
    )
    return response.get("signedURL") or response.get("signed_url") or ""


def delete_invoice_file(storage_path: str) -> None:
    """Remove a file from storage (e.g. when an invoice is deleted)."""
    client = get_supabase_admin()
    client.storage.from_(BUCKET).remove([storage_path])
