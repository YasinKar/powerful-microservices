import json
import logging
import signal
import sys
import yaml
from pathlib import Path

from confluent_kafka import Consumer

from config import settings
from handlers.user_registered import handle_user_registered
from handlers.user_verified import handle_user_verified


BASE_DIR = Path(__file__).resolve().parent

LOGGING_CONFIG_FILE = BASE_DIR / "logging.yaml"

with open(LOGGING_CONFIG_FILE, "r") as f:
    LOGGING = yaml.safe_load(f)

logging.config.dictConfig(LOGGING)

logger = logging.getLogger(__name__)


HANDLERS = {
    "UserRegistered": handle_user_registered,
    "UserVerified": handle_user_verified,
}

def create_consumer() -> Consumer:
    """Initialize Kafka consumer"""
    consumer_conf = {
        "bootstrap.servers": settings.KAFKA_SERVER,
        "group.id": 'notifications-group',
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,
    }
    consumer = Consumer(consumer_conf)
    consumer.subscribe(["orders", "users"])
    return consumer


def handle_event(event: dict):
    """Dispatch incoming event to Celery tasks"""
    event_type = event.get("event_type")
    payload = event.get("data", {})
    
    handler = HANDLERS.get(event_type)
    if handler:
        logger.info(f"Received event: {event.get("event_id")}")
        handler(payload)
    else:
        logger.warning(f"No handler registered for event type: {event_type}")


def consume():
    """Main consumer loop"""
    consumer = create_consumer()
    logger.info("Notifications service listening for events...")

    def shutdown_handler(sig, frame):
        logger.info("Shutting down gracefully...")
        consumer.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            logger.error(f"Kafka error: {msg.error()}")
            continue

        try:
            event = json.loads(msg.value().decode("utf-8"))
            handle_event(event)
        except json.JSONDecodeError:
            logger.error("Invalid JSON message received")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    consume()