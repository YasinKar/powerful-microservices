import json
import logging

from confluent_kafka import Consumer
from sqlmodel import Session

from core.db import engine
from core.config import settings
from services.product_service import ProductService


logging.basicConfig(
level=logging.INFO,
format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    consumer_conf = {
        "bootstrap.servers": settings.KAFKA_SERVER,
        "group.id": "product-service",
        "auto.offset.reset": "earliest"
    }

    consumer = Consumer(consumer_conf)
    consumer.subscribe(["orders"])
    
    logger.info("Product service listening for order events...")

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

                with Session(engine) as session:
                    if event_type == "OrderPlaced":
                        order_items = data.get("order_items", [])

                        for item in order_items:
                            product_id = item.get("product_id")
                            quantity = item.get("quantity", 0)
                            if product_id and quantity > 0:
                                ProductService.update_stock(session, product_id, -quantity)

                    elif event_type == "OrderCancelled":
                        order_items = data.get("order_items", [])

                        for item in order_items:
                            product_id = item.get("product_id")
                            quantity = item.get("quantity", 0)
                            if product_id and quantity > 0:
                                ProductService.update_stock(session, product_id, +quantity)

            except Exception as e:
                logger.error(f"Failed to process message: {e}")
    except KeyboardInterrupt:
        logger.info("Stopping consumer")
    finally:
        consumer.close()
        

if __name__ == "__main__":
    main()