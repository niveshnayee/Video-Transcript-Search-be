from pydantic import BaseSettings
from app.constants import LogLevel


class AppConfig(BaseSettings):
    # Database
    mongo_username: str
    mongo_password: str
    database_name: str
    mongodb_uri: str

    # CORS
    allowed_origins: str = "http://localhost:4200"

    # Logging
    log_level: LogLevel = LogLevel.INFO

    class Config:
        env_file = ".env"