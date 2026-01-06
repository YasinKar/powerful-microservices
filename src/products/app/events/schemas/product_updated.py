from dataclasses import dataclass, asdict

from .base import BaseEvent, ProductEventDTO


@dataclass
class ProductUpdatedPayload:
    product: ProductEventDTO


class ProductUpdatedEvent:
    EVENT_TYPE = "ProductUpdated"

    @staticmethod
    def create(payload: ProductUpdatedPayload) -> BaseEvent:
        return BaseEvent.new(
            event_type=ProductUpdatedEvent.EVENT_TYPE,
            data=asdict(payload),
        )