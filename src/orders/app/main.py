import logging
import logging.config
import yaml

from fastapi import FastAPI
from fastapi.routing import APIRoute

from core.config import settings
from routes.main import api_router


with open(settings.LOGGING_CONFIG_FILE, "r") as f:
    LOGGING = yaml.safe_load(f)

if settings.ENVIRONMENT == "local":
    LOGGING["loggers"][""]["handlers"] = ["console_dev"]
else:
    LOGGING["loggers"][""]["handlers"] = ["console_json", "file_json"]

logging.config.dictConfig(LOGGING)

logger = logging.getLogger(__name__)


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


app = FastAPI(
    title="orders_service",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

app.include_router(api_router, prefix=settings.API_V1_STR)
