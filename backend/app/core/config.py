"""
core/config.py
──────────────
Centralised configuration using pydantic-settings.
All values are read from environment variables / .env file.
"""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore any unrecognised env vars
    )

    # ── App ──────────────────────────────────────────────────
    app_env: str = "development"
    secret_key: str = "change-me-in-production"
    allowed_origins: list[str] = ["http://localhost:3000"]

    # ── Supabase ─────────────────────────────────────────────
    supabase_url: str
    supabase_key: str
    supabase_service_role_key: str
    supabase_jwt_secret: str

    # ── Groq ─────────────────────────────────────────────────
    groq_api_key: str
    groq_model: str = "llama-3.3-70b-versatile"

    # ── Neo4j ────────────────────────────────────────────────
    neo4j_uri: str
    neo4j_username: str
    neo4j_password: str
    neo4j_database: str

    # ── Neo4j Aura (optional) ─────────────────────────────────
    aura_instanceid: Optional[str] = None
    aura_instancename: Optional[str] = None

    # ── OCR ──────────────────────────────────────────────────
    tesseract_cmd: str = "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
    poppler_path: Optional[str] = "C:\\Program Files\\poppler\\poppler-25.12.0\\Library\\bin"

    # ── Storage ──────────────────────────────────────────────
    invoice_upload_dir: str = "./uploads/invoices"
    faiss_index_path: str = "./data/faiss_index"

    @property
    def is_dev(self) -> bool:
        return self.app_env == "development"

    @property
    def is_windows(self) -> bool:
        import platform
        return platform.system() == "Windows"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()