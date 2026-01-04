from typing import Literal, ClassVar
from pathlib import Path

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
    MONGO_HOST: str
    MONGO_PORT: int
    MONGO_INITDB_ROOT_USERNAME: str | None = None
    MONGO_INITDB_ROOT_PASSWORD: str | None = None
    MONGO_INITDB_DATABASE: str

    KEYCLOAK_SERVER_URL: str
    KEYCLOAK_CLIENT_ID: str
    KEYCLOAK_REALM_NAME: str
    KEYCLOAK_CLIENT_SECRET_KEY: str

    KAFKA_SERVER: str


settings = Settings()