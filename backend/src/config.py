from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    postgres_user: str = Field("queue", validation_alias="POSTGRES_USER")
    postgres_password: str = Field("queue", validation_alias="POSTGRES_PASSWORD")
    postgres_db: str = Field("queue", validation_alias="POSTGRES_DB")
    postgres_host: str = Field("postgres", validation_alias="POSTGRES_HOST")
    postgres_port: int = Field(5432, validation_alias="POSTGRES_PORT")

    redis_host: str = Field("redis", validation_alias="REDIS_HOST")
    redis_port: int = Field(6379, validation_alias="REDIS_PORT")

    jwt_secret: str = Field(validation_alias="JWT_SECRET")
    jwt_algorithm: str = Field("HS256", validation_alias="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(1440, validation_alias="JWT_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(30, validation_alias="REFRESH_TOKEN_EXPIRE_DAYS")

    queue_ttl: int = Field(86400, validation_alias="QUEUE_TTL")
    debug: bool = Field(False, validation_alias="DEBUG")

    cors_origins_raw: str = Field("*", validation_alias="CORS_ORIGINS")

    database_url: str = ""
    redis_url: str = ""

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins_raw.split(",") if o.strip()]

    @model_validator(mode="after")
    def build_urls(self) -> Settings:
        if not self.database_url:
            self.database_url = (
                f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            )
        if not self.redis_url:
            self.redis_url = f"redis://{self.redis_host}:{self.redis_port}/0"
        return self
