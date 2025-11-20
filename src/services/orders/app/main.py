import logging
import asyncio

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.routing import APIRoute

from core.config import settings
from routes.main import api_router
from events.outbox_events import publish_outbox_events


logger = logging.getLogger(__name__)


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting outbox publisher...")
    outbox_task = asyncio.create_task(publish_outbox_events(max_retries=5, backoff_seconds=5))
    
    yield
    
    logger.info("Shutting down outbox publisher task...")
    outbox_task.cancel() 
    try:
        await outbox_task
    except asyncio.CancelledError:
        logger.info("Outbox task cancelled successfully")


app = FastAPI(
    title="orders_service",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan
)

app.include_router(api_router, prefix=settings.API_V1_STR)