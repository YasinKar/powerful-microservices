from uuid import UUID
from dataclasses import dataclass, asdict
from typing import List

from .base import BaseEvent, OrderItemDTO


@dataclass
class OrderCancelledPayload:
    order_items: List[OrderItemDTO]
    order_id: UUID


class OrderCancelledEvent:
    EVENT_TYPE = "OrderCancelled"

    @staticmethod
    def create(payload: OrderCancelledPayload) -> BaseEvent:
        return BaseEvent.new(
            event_type=OrderCancelledEvent.EVENT_TYPE,
            data=asdict(payload),
        )