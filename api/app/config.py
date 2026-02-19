# app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # Application
    app_name: str = "E-Commerce Order System API"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://orderuser:orderpass@postgres:5432/orders_db"
    database_test_url: Optional[str] = None

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # Kafka
    kafka_bootstrap_servers: str = "kafka:29092"
    kafka_group_id: str = "order-system-group"

    # JWT
    jwt_secret_key: str = "your-super-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 100
    rate_limit_order_create: int = 20
    rate_limit_webhook_register: int = 10

    # Webhook
    webhook_secret: str = "your-webhook-secret"
    webhook_max_retries: int = 3
    webhook_retry_delay_seconds: int = 60

    # Monitoring
    prometheus_enabled: bool = True
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
