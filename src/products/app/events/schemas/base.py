from dataclasses import dataclass, asdict
from datetime import datetime
from uuid import uuid4, UUID
from typing import Any, Dict, Optional

from models.product import Product


@dataclass
class BaseEvent:
    event_id: str
    event_type: str
    occurred_at: str
    data: Dict[str, Any]
    version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def new(cls, **kwargs):
        return cls(
            event_id=str(uuid4()),
            occurred_at=datetime.utcnow().isoformat(),
            **kwargs
        )
    

@dataclass
class ProductEventDTO:
    id: UUID
    name: str
    description: Optional[str]
    price: int
    stock: int
    category_id: UUID
    brand_id: UUID
    is_active: bool
    rating: Optional[float]

    @classmethod
    def from_model(cls, product: Product) -> "ProductEventDTO":
        return cls(
            id=product.id,
            name=product.name,
            description=product.description,
            price=product.price,
            stock=product.stock,
            category_id=product.category_id,
            brand_id=product.brand_id,
            is_active=product.is_active,
            rating=product.rating,
        )