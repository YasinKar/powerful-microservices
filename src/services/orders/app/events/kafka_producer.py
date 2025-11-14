import json
import logging

from confluent_kafka import Producer

from core.config import settings


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


producer_config = {
    "bootstrap.servers": settings.KAFKA_SERVER,
}


producer = Producer(producer_config)


def delivery_report(err, msg):
    if err is not None:
        logger.error(f"Delivery failed for record {msg.key()}: {err}")
    else:
        logger.info(f"Record successfully produced to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")


def publish_event(topic: str, value: dict):
    try:
        producer.produce(
            topic=topic,
            value=json.dumps(value, default=str),
            callback=delivery_report
        )
        producer.flush()
    except Exception as e:
        logger.error(f"Error producing Kafka message: {e}")
