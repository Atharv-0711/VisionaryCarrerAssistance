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


settings = Settings()
