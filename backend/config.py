import os
from typing import Optional


class Settings:
    """Centralized configuration read from environment variables."""

    def __init__(self) -> None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.database_path: str = os.getenv(
            "DATABASE_PATH",
            os.path.join(base_dir, "surveys.db"),
        )

        # Postgres + pgvector configuration (optional; used for mentor matching)
        self.pg_dsn: Optional[str] = os.getenv("PG_DSN")
        self.pg_vector_dim: int = int(os.getenv("PG_VECTOR_DIM", "384"))

        # Redis / Celery
        self.redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.celery_broker_url: str = os.getenv(
            "CELERY_BROKER_URL", self.redis_url
        )
        self.celery_backend_url: str = os.getenv(
            "CELERY_BACKEND_URL", self.redis_url
        )

        # SMTP / email configuration
        self.smtp_server: Optional[str] = os.getenv("SMTP_SERVER")
        self.smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username: Optional[str] = os.getenv("SMTP_USERNAME")
        self.smtp_password: Optional[str] = os.getenv("SMTP_PASSWORD")
        self.smtp_use_tls: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        self.default_sender: Optional[str] = os.getenv(
            "MAIL_DEFAULT_SENDER", self.smtp_username
        )

        # Frontend URL used in email links
        self.frontend_base_url: str = os.getenv(
            "FRONTEND_BASE_URL", "http://localhost:5173"
        )

        # SMS (Twilio)
        self.twilio_account_sid: Optional[str] = os.getenv("TWILIO_ACCOUNT_SID")
        self.twilio_auth_token: Optional[str] = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_from_number: Optional[str] = os.getenv("TWILIO_FROM_NUMBER")

        # Data quality monitoring defaults
        self.data_quality_default_schema_version: str = os.getenv(
            "DQ_DEFAULT_SCHEMA_VERSION", "v1"
        )
        self.dq_threshold_completeness_min: float = float(
            os.getenv("DQ_THRESHOLD_COMPLETENESS_MIN", "0.9")
        )
        self.dq_threshold_duplicates_max: int = int(
            os.getenv("DQ_THRESHOLD_DUPLICATES_MAX", "0")
        )
        self.dq_threshold_outliers_max: int = int(
            os.getenv("DQ_THRESHOLD_OUTLIERS_MAX", "5")
        )
        self.dq_alert_email_to = [
            email.strip()
            for email in os.getenv("DQ_ALERT_EMAIL_TO", "").split(",")
            if email.strip()
        ]
        self.dq_alert_webhook_urls = [
            url.strip()
            for url in os.getenv("DQ_ALERT_WEBHOOK_URLS", "").split(",")
            if url.strip()
        ]
        self.dq_alert_slack_webhook: Optional[str] = os.getenv("DQ_ALERT_SLACK_WEBHOOK")

        # Analytics API performance controls
        self.analytics_cache_ttl_seconds: int = int(
            os.getenv("ANALYTICS_CACHE_TTL_SECONDS", "120")
        )
        self.analytics_cache_enabled: bool = (
            os.getenv("ANALYTICS_CACHE_ENABLED", "true").lower() == "true"
        )
        self.analytics_max_page_size: int = int(
            os.getenv("ANALYTICS_MAX_PAGE_SIZE", "100")
        )
        self.analytics_default_page_size: int = int(
            os.getenv("ANALYTICS_DEFAULT_PAGE_SIZE", "25")
        )
        self.analytics_rate_limit_requests: int = int(
            os.getenv("ANALYTICS_RATE_LIMIT_REQUESTS", "120")
        )
        self.analytics_rate_limit_window_seconds: int = int(
            os.getenv("ANALYTICS_RATE_LIMIT_WINDOW_SECONDS", "60")
        )

        # Operational readiness signals
        self.monitoring_slow_request_ms: int = int(
            os.getenv("MONITORING_SLOW_REQUEST_MS", "1500")
        )


settings = Settings()
