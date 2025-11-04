import logging
from typing import Optional, List

from models.order import Order
from core.mongodb import db

logger = logging.getLogger(__name__)


class OrderService:
    collection = db["orders"]

    @staticmethod
    async def create_order(order_data: dict) -> Order:
        """Create a new order"""
        order = Order(**order_data)
        order.calculate_total()
        await OrderService.collection.insert_one(order.to_dict())
        logger.info(f"Order created for user {order.user_id}")
        return order

    @staticmethod
    async def get_order(user_id: str, order_id: str) -> Optional[Order]:
        """Get a specific order by user_id and order_id"""
        data = await OrderService.collection.find_one({"user_id": user_id, "id": order_id})
        return Order.from_mongo(data)

    @staticmethod
    async def get_orders(user_id: str, status: Optional[str] = None) -> List[Order]:
        """Get all orders of a user (optionally filtered by status)"""
        query = {"user_id": user_id}
        if status:
            query["status"] = status
        cursor = OrderService.collection.find(query).sort("created_at", -1)
        orders = [Order.from_mongo(doc) async for doc in cursor]
        return orders

    @staticmethod
    async def cancel_order(user_id: str, order_id: str) -> bool:
        """Cancel an order if it’s still pending"""
        order = await OrderService.collection.find_one({"user_id": user_id, "id": order_id})
        if not order:
            return False
        if order.get("status") not in ["pending", "paid"]:
            return False  # Can't cancel shipped or delivered orders

        result = await OrderService.collection.update_one(
            {"id": order_id, "user_id": user_id},
            {"$set": {"status": "canceled", "updated_at": Order.now()}}
        )
        return result.modified_count > 0