import pytest

from events.handlers import order_cancelled, order_placed


def test_handle_order_placed_updates_stock_and_commits(monkeypatch):
    updated = []
    consumer = type("Consumer", (), {"commit": lambda self, msg: updated.append(("commit", msg))})()

    monkeypatch.setattr(
        order_placed.ProductService,
        "update_stock",
        lambda session, product_id, quantity_change: updated.append((product_id, quantity_change)),
    )

    payload = {
        "data": {
            "order_id": "o1",
            "order_items": [
                {"product_id": "p1", "quantity": 2},
                {"product_id": "p2", "quantity": 1},
            ],
        }
    }

    order_placed.handle_order_placed(object(), payload, consumer, "msg")

    assert ("p1", -2) in updated
    assert ("p2", -1) in updated
    assert ("commit", "msg") in updated


def test_handle_order_placed_publishes_failure_event(monkeypatch):
    monkeypatch.setattr(
        order_placed.ProductService,
        "update_stock",
        lambda session, product_id, quantity_change: (_ for _ in ()).throw(RuntimeError("insufficient")),
    )
    published = []
    monkeypatch.setattr(order_placed, "publish_event", lambda topic, value: published.append((topic, value)))

    payload = {
        "data": {
            "order_id": "o1",
            "order_items": [{"product_id": "p1", "quantity": 2}],
        }
    }

    with pytest.raises(RuntimeError):
        order_placed.handle_order_placed(object(), payload, object(), "msg")

    assert published
    assert published[0][0] == "order_failures"


def test_handle_order_cancelled_updates_stock_and_commits(monkeypatch):
    updated = []
    consumer = type("Consumer", (), {"commit": lambda self, msg: updated.append(("commit", msg))})()
    monkeypatch.setattr(
        order_cancelled.ProductService,
        "update_stock",
        lambda session, product_id, quantity_change: updated.append((product_id, quantity_change)),
    )
    payload = {
        "data": {
            "order_items": [
                {"product_id": "p1", "quantity": 2},
                {"product_id": "p2", "quantity": 1},
            ],
        }
    }

    order_cancelled.handle_order_cancelled(object(), payload, consumer, "msg")

    assert ("p1", 2) in updated
    assert ("p2", 1) in updated
    assert ("commit", "msg") in updated
