from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    redis_url: str = Field("redis://redis:6379/0", validation_alias="REDIS_URL")
    database_url: str = Field(validation_alias="DATABASE_URL")
    jwt_secret: str = Field(validation_alias="JWT_SECRET")
    jwt_algorithm: str = Field("HS256", validation_alias="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(1440, validation_alias="JWT_EXPIRE_MINUTES")
    queue_ttl: int = Field(86400, validation_alias="QUEUE_TTL")
    refresh_token_expire_days: int = Field(30, validation_alias="REFRESH_TOKEN_EXPIRE_DAYS")
    cors_origins: list[str] = Field(default=["*"], validation_alias="CORS_ORIGINS")
