from pydantic import BaseSettings


class R2Config(BaseSettings):
    account_id: str
    access_key_id: str
    secret_access_key: str
    bucket_name: str

    class Config:
        env_file = ".env"
        env_prefix = "R2_"