import json
import logging
from datetime import datetime, timezone

from confluent_kafka import Consumer

from core.config import settings
from services.product_service import ProductService
from services.order_service import OrderService


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def main():
    consumer_conf = {
        "bootstrap.servers": settings.KAFKA_SERVER,
        "group.id": "order-service",
        "auto.offset.reset": "earliest"
    }

    consumer = Consumer(consumer_conf)
    consumer.subscribe(["products", "order_failures"])
    
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
                topic = msg.topic()
                event_type = data.get("event_type")
                
                # To synchronize products
                if topic == "products":
                    product_data = data.get("product")

                    if event_type == "ProductCreated":
                        ProductService.create_product(product_data)
                    elif event_type == "ProductUpdated":
                        ProductService.update_product(product_data)
                    elif event_type == "ProductDeleted":
                        ProductService.delete_product(product_data)
                    else:
                        logger.warning(f"Unknown event type: {event_type}")
                # To rollback orders on failures
                elif topic == "order_failures":
                    if event_type == "OrderPlacementFailed":
                        order_id = data.get("order_id")
                        correlation_id = data.get("correlation_id")
                        if correlation_id != order_id:  # Optional validation
                            logger.warning("Mismatched correlation_id")
                            continue
                        # Revert order to "failed"
                        result = OrderService.collection.update_one(
                            {"id": order_id},
                            {"$set": {"status": "failed", "updated_at": datetime.now(timezone.utc)}}
                        )
                        if result.modified_count > 0:
                            logger.info(f"Order {order_id} reverted to failed due to placement failure")
                        else:
                            logger.warning(f"Failed to revert order {order_id}")
            except Exception as e:
                logger.error(f"Failed to process message: {e}")
    except KeyboardInterrupt:
        logger.info("Stopping consumer")
    finally:
        consumer.close()
        

if __name__ == "__main__":
    main()