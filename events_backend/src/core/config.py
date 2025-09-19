from functools import lru_cache
from typing import List, Optional

from pydantic import AnyHttpUrl, BaseModel, Field
from dotenv import load_dotenv
import os

# Load .env immediately upon import so early access works
load_dotenv()


class Settings(BaseModel):
    """
    Application runtime settings loaded from environment variables.

    Note:
    - Do not hardcode secrets. Use an .env file to populate these values.
    - See .env.example for required variables.

    Email/notifications:
    - EMAIL_SENDER: optional default 'from' address for outbound emails
    - EMAIL_SMTP_URL: optional SMTP URL should a real SMTP email service be plugged later
    """
    ENV: str = Field(default=os.getenv("ENV", "development"), description="Runtime environment")
    DEBUG: bool = Field(default=os.getenv("DEBUG", "false").lower() == "true", description="Debug mode")

    # Network
    HOST: str = Field(default=os.getenv("HOST", "0.0.0.0"), description="Host address to bind the server")
    PORT: int = Field(default=int(os.getenv("PORT", "3001")), description="Port to bind the server")

    # CORS
    CORS_ALLOW_ORIGINS: List[str] = Field(
        default_factory=lambda: os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
        description="Allowed origins for CORS (comma separated)."
    )

    # Weather integration placeholders
    WEATHER_API_BASE_URL: Optional[AnyHttpUrl] = Field(
        default=os.getenv("WEATHER_API_BASE_URL") or None,
        description="Base URL of the weather API provider"
    )
    WEATHER_API_KEY: Optional[str] = Field(
        default=os.getenv("WEATHER_API_KEY") or None,
        description="API key for the weather provider"
    )

    # Email/notification placeholders
    EMAIL_SENDER: Optional[str] = Field(default=os.getenv("EMAIL_SENDER") or None, description="Default sender email")
    EMAIL_SMTP_URL: Optional[str] = Field(default=os.getenv("EMAIL_SMTP_URL") or None, description="SMTP connection URL")

    # Site URL for redirects
    SITE_URL: Optional[AnyHttpUrl] = Field(
        default=os.getenv("SITE_URL") or None,
        description="Public site base URL"
    )


@lru_cache
def get_settings() -> Settings:
    """
    PUBLIC_INTERFACE
    Returns the cached application settings instance.

    Ensures that .env is considered and provides an immutable config object.
    """
    return Settings()
