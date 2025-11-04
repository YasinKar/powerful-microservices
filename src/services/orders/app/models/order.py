from datetime import datetime, timezone
from typing import List
import uuid

from pydantic import BaseModel, Field

from .cart import CartItem
from .address import UserAddress


class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    items: List[CartItem]
    shipping_address: UserAddress
    total_price: float = 0.0
    status: str = "pending"  # pending, paid, shipped, delivered, canceled
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def calculate_total(self):
        self.total_price = sum((item.price or 0) * item.quantity for item in self.items)
        return self.total_price

    def to_dict(self):
        return self.model_dump()

    @classmethod
    def from_mongo(cls, data):
        if not data:
            return None
        data["id"] = data.get("id") or str(data.get("_id"))
        data.pop("_id", None)
        return cls(**data)
