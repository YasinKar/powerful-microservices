from dataclasses import dataclass, asdict

from .base import BaseEvent, ProductEventDTO


@dataclass
class ProductDeletedPayload:
    product: ProductEventDTO


class ProductDeletedEvent:
    EVENT_TYPE = "ProductDeleted"

    @staticmethod
    def create(payload: ProductDeletedPayload) -> BaseEvent:
        return BaseEvent.new(
            event_type=ProductDeletedEvent.EVENT_TYPE,
            data=asdict(payload),
        )