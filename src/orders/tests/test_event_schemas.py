from events.schemas.base import BaseEvent, OrderItemDTO
from events.schemas.order_cancelled import OrderCancelledEvent, OrderCancelledPayload
from events.schemas.order_placed import OrderPlacedEvent, OrderPlacedPayload


def test_base_event_factory():
    event = BaseEvent.new(event_type="X", data={"a": 1})
    assert event.event_type == "X"
    assert event.data["a"] == 1


def test_order_item_dto_from_dict():
    dto = OrderItemDTO.from_dict({"id": "i1", "product_id": "p1", "quantity": 2})
    assert dto.product_id == "p1"


def test_order_placed_event_factory():
    payload = OrderPlacedPayload(order_items=[OrderItemDTO(id="i1", product_id="p1", quantity=1)], order_id="o1")
    event = OrderPlacedEvent.create(payload)
    assert event.event_type == "OrderPlaced"


def test_order_cancelled_event_factory():
    payload = OrderCancelledPayload(order_items=[OrderItemDTO(id="i1", product_id="p1", quantity=1)], order_id="o1")
    event = OrderCancelledEvent.create(payload)
    assert event.event_type == "OrderCancelled"
