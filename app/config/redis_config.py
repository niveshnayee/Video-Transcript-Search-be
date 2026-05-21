try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic.v1 import BaseSettings


class RedisConfig(BaseSettings):
    url: str = "redis://localhost:6379/0"

    class Config:
        env_file = ".env"
        env_prefix = "REDIS_"
