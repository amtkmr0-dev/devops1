from typing import Optional


class Settings:
    # Database
    database_url: str = "sqlite:///./data/dividend_scanner.db"

    # API Keys
    alpha_vantage_api_key: Optional[str] = None
    fyers_client_id: Optional[str] = None
    fyers_secret_key: Optional[str] = None
    fyers_redirect_uri: str = "https://127.0.0.1"

    # Email Configuration
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    email_username: Optional[str] = None
    email_password: Optional[str] = None

    # Application Settings
    debug: bool = True
    log_level: str = "INFO"
    data_update_interval_hours: int = 6
    min_dividend_yield: float = 1.0
    max_payout_ratio: float = 100.0

    # Cache Settings
    cache_expiry_hours: int = 1

    def __init__(self):
        # Load from environment variables or use defaults
        import os
        self.database_url = os.getenv(
            "DATABASE_URL", "sqlite:///./data/dividend_scanner.db")
        self.alpha_vantage_api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        self.fyers_client_id = os.getenv("FYERS_CLIENT_ID")
        self.fyers_secret_key = os.getenv("FYERS_SECRET_KEY")
        self.fyers_redirect_uri = os.getenv(
            "FYERS_REDIRECT_URI", "https://127.0.0.1")
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.email_username = os.getenv("EMAIL_USERNAME")
        self.email_password = os.getenv("EMAIL_PASSWORD")
        self.debug = os.getenv("DEBUG", "True").lower() == "true"
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.data_update_interval_hours = int(
            os.getenv("DATA_UPDATE_INTERVAL_HOURS", "6"))
        self.min_dividend_yield = float(os.getenv("MIN_DIVIDEND_YIELD", "1.0"))
        self.max_payout_ratio = float(os.getenv("MAX_PAYOUT_RATIO", "100.0"))
        self.cache_expiry_hours = int(os.getenv("CACHE_EXPIRY_HOURS", "1"))


# Global settings instance
settings = Settings()
