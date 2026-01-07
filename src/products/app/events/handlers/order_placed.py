import logging

from services.product_service import ProductService
from events.kafka_producer import publish_event
from events.schemas.order_placement_failed import OrderPlacementFailedEvent, OrderPlacementFailedPayload


logger = logging.getLogger(__name__)


def handle_order_placed(session, data, consumer, msg):
    try:
        order_items = data.get("data").get("order_items", [])
        order_id = data.get("data").get("order_id")

        for item in order_items:
            product_id = item.get("product_id")
            quantity = item.get("quantity", 0)

            if product_id and quantity > 0:
                ProductService.update_stock(session, product_id, -quantity)

        consumer.commit(msg)

    except Exception as e:
        payload = OrderPlacementFailedPayload(
            error=str(e),
            order_id=order_id
        )
        failure_event = OrderPlacementFailedEvent.create(payload)

        publish_event(
            topic="order_failures",
            value=failure_event.to_dict()
        )

        logger.error(f"OrderPlaced handler error: {e}")
        raise
