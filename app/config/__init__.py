from app.config.app_config import AppConfig
from app.config.r2_config import R2Config
from app.config.redis_config import RedisConfig

# Load configurations
app_config = AppConfig()
r2_config = R2Config()
redis_config = RedisConfig()

__all__ = ["app_config", "r2_config", "redis_config"]