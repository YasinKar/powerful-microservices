import logging
from typing import Optional

from models.cart import Cart, CartItem
from core.mongodb import db
from services.product_service import ProductService


logger = logging.getLogger(__name__)


class CartService:
    collection = db["carts"]

    @staticmethod
    async def create_cart(user_id: str) -> Cart:
        existing = CartService.collection.find_one({"user_id": user_id})
        if existing:
            return Cart.from_mongo(existing)

        cart = Cart(user_id=user_id, items=[], total_price=0)
        res = CartService.collection.insert_one(cart.to_dict())
        cart.id = str(res.inserted_id)
        return cart

    @staticmethod
    async def get_cart(user_id: str) -> Optional[Cart]:
        cart = CartService.collection.find_one({"user_id": user_id})
        if not cart:
            return None
        return Cart.from_mongo(cart)

    @staticmethod
    async def create_cart_item(user_id: str, product_id: str, quantity: int) -> Cart:
        """Add or update an item in the user's cart"""
        cart_data = CartService.collection.find_one({"user_id": user_id})
        if not cart_data:
            cart = Cart(user_id=user_id, items=[], total_price=0)
        else:
            cart = Cart.from_mongo(cart_data)

        product = ProductService.get_product(product_id)
        print(product)
        if not product:
            return {
                "error" : "Product not found"
            }

        existing_item = next((i for i in cart.items if i.product_id == product_id), None)

        if existing_item:
            if product["stock"] < quantity + existing_item.quantity:
                return {
                    "error" : f"Only {product["stock"]} items available in stock."
                }
            
            existing_item.quantity += quantity
        else:
            if product["stock"] < quantity:
                return {
                    "error" : f"Only {product["stock"]} items available in stock."
                }

            cart.items.append(CartItem(product_id=product_id, quantity=quantity))

        cart.calculate_total()

        CartService.collection.update_one(
            {"user_id": user_id},
            {"$set": cart.to_dict()},
            upsert=True
        )

        return cart

    @staticmethod
    async def delete_cart_item(user_id: str, item_id: str) -> Optional[Cart]:
        """Remove an item from user's cart"""
        cart_data = CartService.collection.find_one({"user_id": user_id})
        if not cart_data:
            return None

        cart = Cart.from_mongo(cart_data)

        updated_items = [item for item in cart.items if item.id != item_id]

        if len(updated_items) == len(cart.items):
            return cart

        cart.items = updated_items
        cart.calculate_total()

        CartService.collection.update_one(
            {"user_id": user_id},
            {"$set": cart.to_dict()}
        )

        return cart

    @staticmethod
    async def delete_cart(user_id: str) -> bool:
        """Delete entire cart"""
        result = CartService.collection.delete_one({"user_id": user_id})
        return result.deleted_count > 0