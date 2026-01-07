import logging

from services.product_service import ProductService


logger = logging.getLogger(__name__)


def handle_order_cancelled(session, data, consumer, msg):
    try:
        order_items = data.get("data").get("order_items", [])

        for item in order_items:
            product_id = item.get("product_id")
            quantity = item.get("quantity", 0)

            if product_id and quantity > 0:
                ProductService.update_stock(session, product_id, +quantity)

        consumer.commit(msg)

    except Exception as e:
        logger.error(f"OrderCancelled handler error: {e}")
        raise
