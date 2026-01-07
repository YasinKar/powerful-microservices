from uuid import UUID
from dataclasses import dataclass, asdict
from typing import List

from .base import BaseEvent
from models.order import CartItem


@dataclass
class OrderPlacedPayload:
    order_items: List[CartItem]
    order_id: UUID


class OrderPlacedEvent:
    EVENT_TYPE = "OrderPlaced"

    @staticmethod
    def create(payload: OrderPlacedPayload) -> BaseEvent:
        return BaseEvent.new(
            event_type=OrderPlacedEvent.EVENT_TYPE,
            data=asdict(payload),
        )