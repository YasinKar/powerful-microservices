import uuid
from dataclasses import dataclass, asdict

from .base import BaseEvent


@dataclass
class OrderPlacementFailedPayload:
    order_id: uuid.UUID
    error: str


class OrderPlacementFailedEvent:
    EVENT_TYPE = "OrderPlacementFailed"

    @staticmethod
    def create(payload: OrderPlacementFailedPayload) -> BaseEvent:
        return BaseEvent.new(
            event_type=OrderPlacementFailedEvent.EVENT_TYPE,
            data=asdict(payload),
        )