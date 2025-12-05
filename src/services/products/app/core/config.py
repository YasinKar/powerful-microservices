from typing import Literal, ClassVar
from pathlib import Path

from pydantic import (
    PostgresDsn,
    computed_field,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BASE_DIR: ClassVar[Path] = Path(__file__).resolve().parent.parent.parent

    LOGGING_CONFIG_FILE: ClassVar[Path] = Path(__file__).resolve().parent.parent / "logging.yaml"

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),    
        env_ignore_empty=True,
        extra="ignore",
    )

    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: Literal["local", "production"] = "local"

    # Database 
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )
    
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None
    REDIS_URL: str | None = None

    KEYCLOAK_SERVER_URL: str
    KEYCLOAK_CLIENT_ID: str
    KEYCLOAK_REALM_NAME: str
    KEYCLOAK_CLIENT_SECRET_KEY: str

    KAFKA_SERVER: str


settings = Settings()