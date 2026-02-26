import asyncio
import logging.config
import yaml

from core.config import settings
from events.outbox_events import publish_outbox_events


with open(settings.LOGGING_CONFIG_FILE, "r") as f:
    LOGGING = yaml.safe_load(f)

if settings.ENVIRONMENT == "local":
    LOGGING["loggers"][""]["handlers"] = ["console_dev"]
else:
    LOGGING["loggers"][""]["handlers"] = ["console_json", "file_json"]

logging.config.dictConfig(LOGGING)

logger = logging.getLogger(__name__)


def main():
    logger.info("Starting orders outbox worker...")
    asyncio.run(publish_outbox_events(max_retries=5, backoff_seconds=5))


if __name__ == "__main__":
    main()
