"""Application configuration loaded from environment variables.

Unified config for PakMind backend — merges PakGuide, PakWatch, and PakScholar settings.
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings
from functools import lru_cache

# backend/ directory — anchors the .env lookup regardless of CWD
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """All configuration values required by the PakMind unified backend."""

    # Supabase (shared PakMind database)
    supabase_url: str = ""
    supabase_key: str = ""
    # Service-role key for write operations (used by PakScholar seed/admin)
    supabase_secret_key: str = ""

    # Google Gemini (FREE — primary LLM + embeddings)
    google_api_key: str = ""
    # Backup Gemini key — from a DIFFERENT Google account/project
    google_api_key_2: str = ""

    # Groq (FREE — verification LLM)
    groq_api_key: str = ""

    # Serper.dev (FREE — Google search for PakGuide + PakWatch + PakScholar)
    serper_api_key: str = ""

    # OpenAI (OPTIONAL — paid fallback)
    openai_api_key: str = ""

    # Model selection (all free-tier defaults)
    primary_llm: str = "google"
    verification_llm: str = "groq"
    embedding_provider: str = "google"
    embedding_model: str = "gemini-embedding-001"
    embedding_dimensions: int = 1536
    gemini_model: str = "gemini-3.6-flash"
    groq_model: str = "qwen/qwen3.8-27b"
    llm_model: str = "gpt-4o-mini"
    # PakScholar uses a lighter model for eligibility matching
    scholar_model: str = "gemini-2.0-flash"

    # Retrieval
    vector_top_k: int = 5
    keyword_top_k: int = 5

    # CORS — comma-separated origins
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Rate limiting
    rate_limit_per_minute: int = 20
    rate_limit_enabled: bool = True

    # Web-answer cache (PakWatch out-of-DB fallback)
    web_answer_ttl_hours: int = 168  # 7 days
    web_answer_sim_threshold: float = 0.88

    model_config = {
        "env_file": str(BASE_DIR / ".env"),
        "env_file_encoding": "utf-8",
    }

    def get_cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    def google_api_keys(self) -> list[str]:
        """Primary key plus any configured backup key (placeholder-safe)."""
        keys = [self.google_api_key]
        if self.google_api_key_2 and not self.google_api_key_2.startswith("your_"):
            keys.append(self.google_api_key_2)
        return keys

    def validate_required(self) -> list[str]:
        missing: list[str] = []
        if not self.supabase_url or self.supabase_url.startswith("your_"):
            missing.append("SUPABASE_URL")
        if not self.supabase_key or self.supabase_key.startswith("your_"):
            missing.append("SUPABASE_KEY")
        if not self.google_api_key or self.google_api_key.startswith("your_"):
            missing.append("GOOGLE_API_KEY")
        if not self.groq_api_key or self.groq_api_key.startswith("your_"):
            missing.append("GROQ_API_KEY")
        return missing


@lru_cache
def get_settings() -> Settings:
    return Settings()
