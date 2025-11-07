import uuid
from typing import List

from pydantic import BaseModel, field_validator, Field

from services.product_service import ProductService


class CartItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_id: str
    quantity: int = 1

    def subtotal(self) -> float:
        product = ProductService.get_product(self.product_id)
        return (product["price"] or 0) * self.quantity


class Cart(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    items: List[CartItem] = []
    total_price: float = 0.0

    def calculate_total(self):
        self.total_price = sum(item.subtotal() for item in self.items)
        return self.total_price

    @field_validator('items', mode='before')
    @classmethod
    def validate_items(cls, v, info):
        if not isinstance(v, list):
            raise ValueError("Items must be a list")
        return v

    @classmethod
    def from_mongo(cls, data):
        """Convert from MongoDB document"""
        if not data:
            return None
        data['id'] = data.get('id') or str(data.get('_id'))
        data.pop('_id', None)
        return cls(**data)
