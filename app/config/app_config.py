try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic.v1 import BaseSettings
from app.constants import LogLevel


class AppConfig(BaseSettings):
    # Database
    mongo_username: str
    mongo_password: str
    database_name: str
    mongodb_uri: str

    # CORS
    allowed_origins: str = ""
    # Logging
    log_level: LogLevel = LogLevel.INFO

    class Config:
        env_file = ".env"

    @property
    def cors_allowed_origins(self) -> list[str]:
        """Return CORS origins from ALLOWED_ORIGINS as a comma-separated list."""
        return [
            origin.strip()
            for origin in self.allowed_origins.split(",")
            if origin.strip()
        ]
