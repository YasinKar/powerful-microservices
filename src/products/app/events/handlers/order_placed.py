import logging
from services.product_service import ProductService
from events.kafka_producer import publish_event


logger = logging.getLogger(__name__)


def handle_order_placed(session, data, consumer, msg):
    try:
        order_items = data.get("order_items", [])
        correlation_id = data.get("correlation_id")

        for item in order_items:
            product_id = item.get("product_id")
            quantity = item.get("quantity", 0)

            if product_id and quantity > 0:
                ProductService.update_stock(session, product_id, -quantity)

        consumer.commit(msg)

    except Exception as e:
        failure_event = {
            "event_type": "OrderPlacementFailed",
            "correlation_id": correlation_id,
            "order_id": correlation_id,
            "error": str(e)
        }

        publish_event(
            topic="order_failures",
            value=failure_event
        )

        logger.error(f"OrderPlaced handler error: {e}")
        raise
