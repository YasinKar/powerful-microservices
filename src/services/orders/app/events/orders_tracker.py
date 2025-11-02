import json
import logging

from confluent_kafka import Consumer

from core.config import settings
from services.product_service import ProductService


def main():
    logger = logging.getLogger(__name__)

    consumer_conf = {
        "bootstrap.servers": settings.KAFKA_SERVER,
        "group.id": "order-service",
        "auto.offset.reset": "earliest"
    }

    consumer = Consumer(consumer_conf)
    consumer.subscribe(["products"])
    
    logger.info("Order service listening for product events...")

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
                event_type = data.get("event_type")
                product_data = data.get("product")

                if event_type == "ProductCreated":
                    ProductService.create_product(product_data)
                elif event_type == "ProductUpdated":
                    ProductService.update_product(product_data)
                elif event_type == "ProductDeleted":
                    ProductService.delete_product(product_data)
                else:
                    logger.warning(f"Unknown event type: {event_type}")
            except Exception as e:
                logger.error(f"Failed to process message: {e}")
    except KeyboardInterrupt:
        logger.info("Stopping consumer")
    finally:
        consumer.close()
        

if __name__ == "__main__":
    main()