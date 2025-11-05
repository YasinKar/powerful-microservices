from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),    
        env_ignore_empty=True,
        extra="ignore",
    )

    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    CELERY_QUEUE_HIGH: str = "notifications_high"
    CELERY_QUEUE_DEFAULT: str = "notifications_default"
    CELERY_QUEUE_LOW: str = "notifications_low"

    CELERY_TASK_TIME_LIMIT: int = 60
    CELERY_TASK_SOFT_TIME_LIMIT: int = 45
    CELERY_WORKER_CONCURRENCY: int = 4
    CELERY_TASK_ACKS_LATE: bool = True
    CELERY_PREFETCH_MULTIPLIER: int = 1

    # ---- SMTP ----
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    SMTP_USE_TLS: bool = True
    SMTP_FROM_NAME: str = "Notification"

    KAFKA_SERVER: str


settings = Settings()
