from pydantic import BaseModel, Field
from typing import List
from datetime import datetime, timezone
from .cart import CartItem
from .address import UserAddress


class Order(BaseModel):
    user_id: str
    items: List[CartItem]
    shipping_address: UserAddress
    total_price: float = 0.0
    status: str = "pending"  # pending, shipped, delivered, canceled
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def calculate_total(self):
        self.total_price = sum((item.price or 0) * item.quantity for item in self.items)
        return self.total_price
