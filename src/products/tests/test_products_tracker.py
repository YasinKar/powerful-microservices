from events import products_tracker


def test_tracker_handlers_registered():
    assert "OrderPlaced" in products_tracker.HANDLERS
    assert "OrderCancelled" in products_tracker.HANDLERS
