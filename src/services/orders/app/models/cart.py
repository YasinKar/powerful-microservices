from pydantic import BaseModel, field_validator
from typing import List, Optional


class CartItem(BaseModel):
    product_id: str
    quantity: int = 1
    price: Optional[float] = None


class Cart(BaseModel):
    user_id: str
    items: List[CartItem] = []
    total_price: float = 0.0

    def calculate_total(self):
        self.total_price = sum(
            (item.price or 0) * item.quantity for item in self.items
        )
        return self.total_price

    @field_validator('items', mode='before')
    @classmethod
    def update_total_price(cls, v, info):
        total = sum((item.get('price', 0) * item.get('quantity', 1)) for item in v)
        info.data['total_price'] = total
        return v