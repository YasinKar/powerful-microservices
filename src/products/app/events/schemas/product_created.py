from dataclasses import dataclass, asdict

from .base import BaseEvent, ProductEventDTO


@dataclass
class ProductCreatedPayload:
    product: ProductEventDTO


class ProductCreatedEvent:
    EVENT_TYPE = "ProductCreated"

    @staticmethod
    def create(payload: ProductCreatedPayload) -> BaseEvent:
        return BaseEvent.new(
            event_type=ProductCreatedEvent.EVENT_TYPE,
            data=asdict(payload),
        )