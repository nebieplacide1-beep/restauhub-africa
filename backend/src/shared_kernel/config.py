from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"

    # Rôle applicatif à privilèges limités (ni superutilisateur, ni
    # propriétaire des tables) : la Row-Level Security ne s'applique jamais à
    # un superutilisateur PostgreSQL, quels que soient ENABLE/FORCE ROW LEVEL
    # SECURITY (voir backend/db/init/01-app-role.sql).
    database_url: str = "postgresql+asyncpg://restauhub_app:restauhub_app@localhost:5432/restauhub"
    # Rôle superutilisateur/propriétaire, réservé aux migrations Alembic (DDL).
    migrations_database_url: str = (
        "postgresql+asyncpg://restauhub:restauhub@localhost:5432/restauhub"
    )
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret_key: str = "change-me-in-every-environment"
    jwt_algorithm: str = "HS256"
    jwt_access_token_ttl_minutes: int = 15
    jwt_refresh_token_ttl_days: int = 30

    two_factor_encryption_key: str = "change-me-fernet-key-44-bytes-base64=="

    frontend_url: str = "http://localhost:3000"
    invitation_ttl_hours: int = 72
    password_reset_ttl_minutes: int = 60
    failed_login_max_attempts: int = 5
    failed_login_lockout_minutes: int = 15

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
