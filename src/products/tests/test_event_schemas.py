from events.schemas.base import BaseEvent, ProductEventDTO
from events.schemas.order_placement_failed import OrderPlacementFailedEvent, OrderPlacementFailedPayload
from events.schemas.product_created import ProductCreatedEvent, ProductCreatedPayload
from events.schemas.product_deleted import ProductDeletedEvent, ProductDeletedPayload
from events.schemas.product_updated import ProductUpdatedEvent, ProductUpdatedPayload
from models.category import Brand, Category
from models.product import Product


def build_product():
    category = Category(name="Category A")
    brand = Brand(name="Brand A")
    return Product(
        name="Phone",
        description="Demo",
        price=1000,
        stock=5,
        category_id=category.id,
        brand_id=brand.id,
        is_active=True,
        rating=4.5,
    )


def test_base_event_factory():
    event = BaseEvent.new(event_type="TestEvent", data={"ok": True})
    assert event.event_type == "TestEvent"
    assert event.data["ok"] is True
    assert event.event_id


def test_product_event_dto_from_model():
    dto = ProductEventDTO.from_model(build_product())
    assert dto.name == "Phone"
    assert dto.price == 1000


def test_product_created_event_factory():
    payload = ProductCreatedPayload(product=ProductEventDTO.from_model(build_product()))
    event = ProductCreatedEvent.create(payload)
    assert event.event_type == "ProductCreated"


def test_product_updated_event_factory():
    payload = ProductUpdatedPayload(product=ProductEventDTO.from_model(build_product()))
    event = ProductUpdatedEvent.create(payload)
    assert event.event_type == "ProductUpdated"


def test_product_deleted_event_factory():
    payload = ProductDeletedPayload(product=ProductEventDTO.from_model(build_product()))
    event = ProductDeletedEvent.create(payload)
    assert event.event_type == "ProductDeleted"


def test_order_placement_failed_event_factory():
    payload = OrderPlacementFailedPayload(order_id=build_product().id, error="stock")
    event = OrderPlacementFailedEvent.create(payload)
    assert event.event_type == "OrderPlacementFailed"
