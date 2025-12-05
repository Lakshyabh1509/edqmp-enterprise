"""
EDQMP Backend Configuration
Centralized settings management using Pydantic
"""

from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # ==========================================================================
    # Application
    # ==========================================================================
    app_name: str = "EDQMP"
    app_version: str = "1.0.0"
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=True, alias="DEBUG")
    
    # API Settings
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")
    
    # Security
    secret_key: str = Field(default="dev-secret-key-change-in-production", alias="SECRET_KEY")
    access_token_expire_minutes: int = 60 * 24  # 24 hours
    
    # CORS
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8501",  # Streamlit
        "https://*.streamlit.app",
    ]
    
    # ==========================================================================
    # Supabase
    # ==========================================================================
    supabase_url: str = Field(default="", alias="SUPABASE_URL")
    supabase_key: str = Field(default="", alias="SUPABASE_KEY")
    supabase_service_key: Optional[str] = Field(default=None, alias="SUPABASE_SERVICE_KEY")
    
    # ==========================================================================
    # Database (Direct connection if needed)
    # ==========================================================================
    database_url: Optional[str] = Field(default=None, alias="DATABASE_URL")
    db_pool_size: int = Field(default=5, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=10, alias="DB_MAX_OVERFLOW")
    
    # ==========================================================================
    # Alerting
    # ==========================================================================
    # Email (SMTP)
    smtp_host: Optional[str] = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: Optional[str] = Field(default=None, alias="SMTP_USER")
    smtp_password: Optional[str] = Field(default=None, alias="SMTP_PASSWORD")
    smtp_from: str = Field(default="noreply@edqmp.io", alias="SMTP_FROM")
    
    # Slack
    slack_webhook_url: Optional[str] = Field(default=None, alias="SLACK_WEBHOOK_URL")
    slack_default_channel: str = Field(default="#data-quality-alerts", alias="SLACK_DEFAULT_CHANNEL")
    
    # PagerDuty
    pagerduty_api_key: Optional[str] = Field(default=None, alias="PAGERDUTY_API_KEY")
    pagerduty_service_id: Optional[str] = Field(default=None, alias="PAGERDUTY_SERVICE_ID")
    
    # ==========================================================================
    # Rate Limiting
    # ==========================================================================
    rate_limit_requests: int = Field(default=100, alias="RATE_LIMIT_REQUESTS")
    rate_limit_period: int = Field(default=60, alias="RATE_LIMIT_PERIOD")  # seconds
    
    # ==========================================================================
    # Logging
    # ==========================================================================
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")
    
    # ==========================================================================
    # Validation Engine
    # ==========================================================================
    default_validation_threshold: float = 0.95
    max_sample_failures: int = 100  # Max failed records to store in details
    validation_timeout_seconds: int = 300
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"
    
    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Export settings instance
settings = get_settings()
