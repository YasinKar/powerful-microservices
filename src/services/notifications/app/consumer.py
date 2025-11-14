import json
import logging
import signal
import sys

from confluent_kafka import Consumer

from config import settings
from tasks.email_tasks import send_welcome_email_task, send_otp_email_task
from tasks.sms_tasks import send_otp_sms_task, send_welcome_sms_task


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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

    if not event_type:
        logger.warning("Event missing type; skipping")
        return

    logger.info(f"Received event: {event_type}")

    try:
        if event_type == "UserRegistered":
            user_type = payload.get("user_type")
            username = payload.get("username")
            otp = payload.get("otp")

            if user_type == "phone":
                send_otp_sms_task.apply_async(
                    args=[username, otp],
                    routing_key="notifications.high",
                    priority=0,
                )

            elif user_type == "email":
                send_otp_email_task.apply_async(
                    args=[username, otp],
                    routing_key="notifications.high",
                    priority=0,
                )

        elif event_type == "UserVerified":
            user_type = payload.get("user_type")
            username = payload.get("username")

            if user_type == "phone":
              send_welcome_sms_task.apply_async(
                    args=[username],
                    routing_key="notifications.default",
                    priority=5,
                )
            elif user_type == "email":
                send_welcome_email_task.apply_async(
                    args=[username],
                    routing_key="notifications.default",
                    priority=5,
                )

        else:
            logger.warning(f"Unknown event type: {event_type}")

    except Exception as e:
        logger.error(f"Failed to process event {event_type}: {e}")


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