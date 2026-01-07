from dataclasses import dataclass, asdict
from datetime import datetime
from uuid import uuid4, UUID
from typing import Any, Dict


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
class OrderItemDTO:
    id: str
    product_id: str
    quantity: int

    @classmethod
    def from_dict(cls, item: dict) -> "OrderItemDTO":
        return cls(
            id=item["id"],
            product_id=item["product_id"],
            quantity=item["quantity"],
        )