import logging
from datetime import datetime, timezone
from services.order_service import OrderService

logger = logging.getLogger(__name__)

def handle_order_failed(data):
    order_id = data.get("order_id")
    correlation_id = data.get("correlation_id")

    if correlation_id != order_id:
        logger.warning("Mismatched correlation_id in order failure")
        return
    
    result = OrderService.collection.update_one(
        {"id": order_id},
        {"$set": {
            "status": "failed",
            "updated_at": datetime.now(timezone.utc),
        }}
    )

    if result.modified_count > 0:
        logger.info(f"Order {order_id} reverted to failed")
    else:
        logger.warning(f"Failed to revert order {order_id}")