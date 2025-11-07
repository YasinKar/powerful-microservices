import logging
from typing import Optional, List
from datetime import datetime, timezone

from fastapi import HTTPException

from models.order import Order
from models.cart import Cart
from services.address_service import AddressService
from core.mongodb import db


logger = logging.getLogger(__name__)


class OrderService:
    collection = db["orders"]

    @staticmethod
    async def create_order(user_id: str, user_cart: Cart, address_id: str) -> Order:
        """Create a new order from the user's current cart"""
        if not user_cart or not user_cart.items:
            raise HTTPException(status_code=400, detail="Cart is empty or invalid")
        
        user_address = await AddressService.get_user_address(address_id, user_id)
        if not user_address:
            raise HTTPException(status_code=404, detail="Address not found")

        order = Order(
            user_id=user_id,
            items=user_cart.items,
            shipping_address=user_address,
        )
        order.calculate_total()
        order.created_at = datetime.now(timezone.utc)
        order.updated_at = datetime.now(timezone.utc)

        result = OrderService.collection.insert_one(order.model_dump())

        logger.info(f"Order created for user {user_id}, id: {result.inserted_id}")

        order.id = str(result.inserted_id)
        return order

    @staticmethod
    async def get_user_current_order(user_id: str) -> Optional[Order]:
        existing = OrderService.collection.find_one({"user_id": user_id, "status": "pending"})
        if existing:
            return Order.from_mongo(existing)

        return None
    
    @staticmethod
    async def get_order(user_id: str, order_id: str) -> Optional[Order]:
        """Get a specific order by user_id and order_id"""
        data = OrderService.collection.find_one({"user_id": user_id, "id": order_id})
        return Order.from_mongo(data)

    @staticmethod
    async def get_orders(user_id: str, status: Optional[str] = None) -> List[Order]:
        """Get all orders of a user (optionally filtered by status)"""
        query = {"user_id": user_id}
        if status:
            query["status"] = status
        cursor = OrderService.collection.find(query).sort("created_at", -1)
        orders = [Order.from_mongo(doc) for doc in cursor]
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
    
    @staticmethod
    async def mark_order_paid(user_id: str, order_id: str) -> Optional[Order]:
        order = OrderService.collection.find_one({"id": order_id, "user_id": user_id})
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        current_status = order.get("status")
        if current_status not in ["pending", "paid"]:
            raise HTTPException(status_code=400, detail=f"Order cannot be marked paid (status={current_status})")

        now = datetime.now(timezone.utc)
        update = {
            "$set": {
                "status": "paid",
                "updated_at": now,
                "paid_at": now
            }
        }

        result = OrderService.collection.update_one({"id": order_id, "user_id": user_id}, update)
        if result.modified_count == 0:
            return None

        updated = OrderService.collection.find_one({"id": order_id, "user_id": user_id})
        return updated