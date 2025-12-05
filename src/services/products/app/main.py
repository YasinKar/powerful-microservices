import logging
import threading
import yaml

from fastapi import FastAPI
from fastapi.routing import APIRoute
from contextlib import asynccontextmanager

from core.config import settings
from routes.main import api_router
from events.outbox_events import publish_outbox_events


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


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting outbox publisher...")
    worker_thread = threading.Thread(
        target=publish_outbox_events, 
        daemon=True
    )
    worker_thread.start()
    
    yield


app = FastAPI(
    title="products_service",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan
)

app.include_router(api_router, prefix=settings.API_V1_STR)