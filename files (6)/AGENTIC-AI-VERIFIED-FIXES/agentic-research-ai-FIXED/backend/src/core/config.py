"""
Core Configuration System
========================

Centralized configuration with:
- Pydantic v2 settings
- Dual mode (Real/Demo)
- Environment variable validation
- Singleton pattern with lru_cache
"""

import os
from functools import lru_cache
from typing import Literal, Optional, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Fix: Remove conflicting environment variables that may cause parsing issues
# These are commonly set by other development tools and can interfere with boolean parsing
for var in ['DEBUG', 'APP_MODE']:
    if var in os.environ:
        val = os.environ[var].lower().strip()
        # Only keep valid boolean strings for DEBUG
        if var == 'DEBUG' and val not in ('true', 'false', '1', '0', 'yes', 'no'):
            del os.environ[var]
        # Only keep valid mode strings for APP_MODE
        elif var == 'APP_MODE' and val not in ('demo', 'real'):
            del os.environ[var]


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Supports dual mode:
    - "demo": LLM-generated synthetic data, no API keys required
    - "real": Connect to actual APIs (PostHog, GA4, etc.)
    """
    
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env", "../../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # =====================
    # Application Settings
    # =====================
    app_name: str = Field(default="Agentic Research AI", description="Application name")
    app_mode: Literal["real", "demo"] = Field(
        default="demo",
        description="Operating mode: 'demo' uses synthetic data, 'real' connects to APIs"
    )
    debug: bool = Field(default=False, description="Enable debug logging")
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Deployment environment"
    )
    
    @field_validator('debug', mode='before')
    @classmethod
    def parse_debug(cls, value):
        """Parse debug value from various formats."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            value = value.lower().strip()
            if value in ('true', '1', 'yes', 'on'):
                return True
            if value in ('false', '0', 'no', 'off', ''):
                return False
        # Default to False for invalid values
        return False
    
    # =====================
    # Authentication
    # =====================
    jwt_secret_key: str = Field(
        default="change-this-jwt-secret-in-production-please",
        description="JWT signing secret"
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm"
    )
    jwt_access_token_expire_minutes: int = Field(
        default=30,
        description="Access token expiry in minutes"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7,
        description="Refresh token expiry in days"
    )
    google_client_id: Optional[str] = Field(
        default=None,
        description="Google OAuth client ID"
    )
    
    # =====================
    # Database Settings
    # =====================
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/agentic_research.db",
        description="Async database URL (SQLite or PostgreSQL)"
    )
    supabase_url: Optional[str] = Field(default=None, description="Supabase project URL")
    supabase_key: Optional[str] = Field(default=None, description="Supabase anon/service key")
    use_supabase: bool = Field(
        default=False,
        description="Use Supabase instead of SQLite"
    )
    
    # =====================
    # Ollama Settings
    # =====================
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama server base URL"
    )
    ollama_model: str = Field(
        default="llama3.2:3b",
        description="Primary Ollama model"
    )
    ollama_fallback_models: str = Field(
        default="qwen2.5-coder:7b,deepseek-r1:8b",
        description="Comma-separated fallback models"
    )
    ollama_timeout: int = Field(default=120, description="Ollama request timeout (seconds)")
    
    # =====================
    # Cloud LLM Settings (Optional)
    # =====================
    openrouter_api_key: Optional[str] = Field(
        default=None,
        description="OpenRouter API key for cloud models"
    )
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key"
    )
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic API key"
    )
    gemini_api_key: Optional[str] = Field(
        default=None,
        description="Google Gemini API key"
    )
    
    # =====================
    # Analytics API Keys (Real Mode)
    # =====================
    posthog_api_key: Optional[str] = Field(
        default=None,
        description="PostHog API key (real mode)"
    )
    posthog_project_id: Optional[str] = Field(
        default=None,
        description="PostHog project ID"
    )
    ga4_project_id: Optional[str] = Field(
        default=None,
        description="Google Cloud project ID for BigQuery GA4"
    )
    ga4_dataset: Optional[str] = Field(
        default="analytics_123456789",
        description="GA4 BigQuery dataset name"
    )
    
    # =====================
    # Research Tools (Real Mode)
    # =====================
    kaggle_username: Optional[str] = Field(
        default=None,
        description="Kaggle username for dataset access"
    )
    kaggle_key: Optional[str] = Field(
        default=None,
        description="Kaggle API key"
    )
    google_credentials_path: Optional[str] = Field(
        default=None,
        description="Path to Google service account credentials JSON"
    )
    sendgrid_api_key: Optional[str] = Field(
        default=None,
        description="SendGrid API key for email connector"
    )
    email_from: str = Field(
        default="noreply@example.com",
        description="Sender address for outgoing emails"
    )
    
    # =====================
    # Memory & Storage
    # =====================
    chromadb_path: str = Field(
        default="./data/chromadb",
        description="ChromaDB persistent storage path"
    )
    redis_url: Optional[str] = Field(
        default="redis://localhost:6379/0",
        description="Redis URL for working memory cache"
    )
    use_redis: bool = Field(default=False, description="Enable Redis for caching")
    
    # =====================
    # Observability
    # =====================
    langfuse_public_key: Optional[str] = Field(
        default=None,
        description="Langfuse public key for tracing"
    )
    langfuse_secret_key: Optional[str] = Field(
        default=None,
        description="Langfuse secret key"
    )
    langfuse_host: str = Field(
        default="https://cloud.langfuse.com",
        description="Langfuse server URL"
    )
    enable_tracing: bool = Field(
        default=False,
        description="Enable LLM tracing with Langfuse"
    )
    
    # =====================
    # API Server Settings
    # =====================
    api_host: str = Field(default="0.0.0.0", description="FastAPI bind host")
    api_port: int = Field(default=8000, description="FastAPI bind port")
    api_workers: int = Field(default=1, description="Uvicorn worker count")
    cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        description="Comma-separated CORS allowed origins"
    )
    
    # =====================
    # ReAct Loop Settings
    # =====================
    max_react_iterations: int = Field(
        default=10,
        description="Maximum ReAct loop iterations per goal"
    )
    checkpoint_frequency: Literal["none", "low", "medium", "high"] = Field(
        default="medium",
        description="How often agent asks for human approval"
    )
    autonomous_mode: Literal["supervised", "partial", "full"] = Field(
        default="supervised",
        description="Agent autonomy level"
    )
    
    # =====================
    # File Upload Limits
    # =====================
    max_upload_size_mb: int = Field(
        default=50,
        description="Maximum file upload size in MB"
    )
    allowed_upload_extensions: str = Field(
        default=".csv,.xlsx,.xls,.json",
        description="Comma-separated allowed file extensions"
    )
    
    # =====================
    # Computed Properties
    # =====================
    
    @property
    def is_demo_mode(self) -> bool:
        """Check if running in demo mode"""
        return self.app_mode == "demo"
    
    @property
    def is_real_mode(self) -> bool:
        """Check if running in real mode"""
        return self.app_mode == "real"
    
    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL (for Alembic migrations)"""
        return self.database_url.replace("+aiosqlite", "")
    
    @property
    def ollama_fallback_list(self) -> List[str]:
        """Parse comma-separated fallback models"""
        return [m.strip() for m in self.ollama_fallback_models.split(",") if m.strip()]
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse comma-separated CORS origins"""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]
    
    @property
    def allowed_extensions_list(self) -> List[str]:
        """Parse comma-separated file extensions"""
        return [e.strip() for e in self.allowed_upload_extensions.split(",") if e.strip()]
    
    # =====================
    # Validation Methods
    # =====================
    
    def validate_real_mode(self) -> None:
        """
        Validate required settings for real mode.
        Raises ValueError if critical keys are missing.
        """
        if not self.is_real_mode:
            return
        
        errors = []
        
        # Check analytics APIs
        if not self.posthog_api_key and not self.ga4_project_id:
            errors.append(
                "Real mode requires at least one analytics API: "
                "posthog_api_key or ga4_project_id"
            )
        
        # Warn about optional APIs
        if not self.kaggle_username or not self.kaggle_key:
            print(
                "Warning: Kaggle credentials not set. "
                "Dataset features will be limited."
            )
        
        if errors:
            raise ValueError(
                f"Configuration errors for real mode:\n" + "\n".join(f"  - {e}" for e in errors)
            )
    
    def get_active_database_url(self) -> str:
        """Get the database URL based on Supabase setting"""
        if self.use_supabase and self.supabase_url:
            # Convert Supabase URL to PostgreSQL URL
            # supabase_url format: https://xxx.supabase.co
            # postgres URL format: postgresql+asyncpg://user:pass@host:5432/postgres
            if self.supabase_key:
                # Extract host from Supabase URL
                host = self.supabase_url.replace("https://", "").replace("http://", "")
                return f"postgresql+asyncpg://postgres:{self.supabase_key}@db.{host}:5432/postgres"
        
        return self.database_url
    
    def model_post_init(self, __context) -> None:
        """Post-initialization validation"""
        if self.is_real_mode:
            try:
                self.validate_real_mode()
            except ValueError as e:
                print(f"Warning: Real mode validation failed: {e}")
                print("Falling back to demo mode...")
                self.app_mode = "demo"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance (singleton pattern).
    
    Usage:
        from src.core.config import get_settings
        
        settings = get_settings()
        if settings.is_demo_mode:
            # Use synthetic data
    """
    return Settings()


# Export for convenience
settings = get_settings()


# =====================
# Constants
# =====================

class Constants:
    """Application constants"""
    
    # Agent Names
    AGENT_DATA = "data_agent"
    AGENT_PRD = "prd_agent"
    AGENT_UIUX = "ui_ux_agent"
    
    # Goal Status
    STATUS_PENDING = "pending"
    STATUS_RUNNING = "running"
    STATUS_CHECKPOINT = "checkpoint"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CANCELLED = "cancelled"
    
    # Checkpoint Types
    CHECKPOINT_SOLUTION_OPTIONS = "solution_options"
    CHECKPOINT_FINAL_APPROVAL = "final_approval"
    CHECKPOINT_BUDGET_EXCEEDED = "budget_exceeded"
    CHECKPOINT_CUSTOM = "custom"
    
    # Memory Types
    MEMORY_WORKING = "working"
    MEMORY_EPISODIC = "episodic"
    MEMORY_SEMANTIC = "semantic"
    MEMORY_PROCEDURAL = "procedural"
    
    # ReAct Loop Actions
    ACTION_THINK = "think"
    ACTION_ACT = "act"
    ACTION_OBSERVE = "observe"
    ACTION_LEARN = "learn"
    
    # File Types
    ALLOWED_IMAGE_TYPES = [".png", ".jpg", ".jpeg", ".gif", ".webp"]
    ALLOWED_DATA_TYPES = [".csv", ".xlsx", ".xls", ".json", ".parquet"]
    ALLOWED_DOC_TYPES = [".pdf", ".docx", ".txt", ".md"]


constants = Constants()
