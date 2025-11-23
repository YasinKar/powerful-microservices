import json
import logging

from confluent_kafka import Consumer

from core.config import settings
from events.handlers.product_created import handle_product_created
from events.handlers.product_updated import handle_product_updated
from events.handlers.product_deleted import handle_product_deleted
from events.handlers.order_failed import handle_order_failed


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


EVENT_HANDLERS = {
    "products": {
        "ProductCreated": handle_product_created,
        "ProductUpdated": handle_product_updated,
        "ProductDeleted": handle_product_deleted,
    },
    "order_failures": {
        "OrderPlacementFailed": handle_order_failed,
    },
}


def main():
    consumer_conf = {
        "bootstrap.servers": settings.KAFKA_SERVER,
        "group.id": "order-service",
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
    }

    consumer = Consumer(consumer_conf)
    consumer.subscribe(["products", "order_failures"])
    
    logger.info("Order service listening for product and failure events...")

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                logger.error(f"Consumer error: {msg.error()}")
                continue

            try:
                data = json.loads(msg.value().decode("utf-8"))
                topic = msg.topic()
                event_type = data.get("event_type")
                logger.info(event_type)

                handler = EVENT_HANDLERS.get(topic, {}).get(event_type)

                if not handler:
                    logger.warning(f"No handler for topic={topic}, event={event_type}")
                    continue

                handler(data)
                consumer.commit(msg)

            except Exception as e:
                logger.error(f"Failed to process message: {e}")

    except KeyboardInterrupt:
        logger.info("Stopping consumer")
    finally:
        consumer.close()


if __name__ == "__main__":
    main()