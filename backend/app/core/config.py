from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_name: str = "AI Resume Platform"
    environment: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    # Public base URL used to register Telegram webhooks (must be HTTPS in prod / tunnel in dev)
    public_base_url: str = "http://localhost:8000"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/ai_resume"
    # Sync URL for Alembic / Celery (psycopg or asyncpg-sync). We reuse asyncpg via async engine in worker.

    # Redis / Celery
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/1"
    celery_result_backend: str = "redis://redis:6379/2"

    # Security
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 14
    # Fernet key (44-char urlsafe base64). Generate: Fernet.generate_key()
    encryption_key: str = "ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg="

    # Storage
    storage_dir: str = "/data/storage"
    max_upload_mb: int = 15

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Seed super-admin (created on first boot if not present)
    superadmin_email: str = "admin@airesume.io"
    superadmin_password: str = "admin12345"
    superadmin_name: str = "Super Admin"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
