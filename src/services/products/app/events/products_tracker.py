import json
import logging.config
import yaml

from confluent_kafka import Consumer
from sqlmodel import Session

from core.db import engine
from core.config import settings
from events.handlers.order_placed import handle_order_placed
from events.handlers.order_cancelled import handle_order_cancelled


with open(settings.LOGGING_CONFIG_FILE, "r") as f:
    LOGGING = yaml.safe_load(f)
    
if settings.ENVIRONMENT == "local":
    LOGGING["loggers"][""]["handlers"] = ["console_dev"]
else:
    LOGGING["loggers"][""]["handlers"] = ["console_json", "file_json"]

logging.config.dictConfig(LOGGING)

logger = logging.getLogger(__name__)


HANDLERS = {
    "OrderPlaced": handle_order_placed,
    "OrderCancelled": handle_order_cancelled,
}


def main():
    consumer_conf = {
        "bootstrap.servers": settings.KAFKA_SERVER,
        "group.id": "product-service",
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
    }

    consumer = Consumer(consumer_conf)
    consumer.subscribe(["orders"])

    logger.info("Product service listening for order events...")

    try:
        while True:
            msg = consumer.poll(1.0)
            if not msg:
                continue
            if msg.error():
                logger.error(f"Consumer error: {msg.error()}")
                continue

            try:
                data = json.loads(msg.value().decode("utf-8"))
                event_type = data.get("event_type")

                handler = HANDLERS.get(event_type)

                if not handler:
                    logger.warning(f"No handler for event: {event_type}")
                    continue

                with Session(engine) as session:
                    handler(session, data, consumer, msg)

            except Exception as e:
                logger.error(f"Failed to process message: {e}")

    except KeyboardInterrupt:
        logger.info("Stopping consumer")

    finally:
        consumer.close()

if __name__ == "__main__":
    main()