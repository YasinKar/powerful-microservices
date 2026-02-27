from events.handlers import order_failed, product_created, product_deleted, product_updated


def test_product_handlers_delegate_to_service(monkeypatch):
    calls = []
    monkeypatch.setattr(product_created.ProductService, "create_product", lambda data: calls.append(("create", data["id"])))
    monkeypatch.setattr(product_updated.ProductService, "update_product", lambda data: calls.append(("update", data["id"])))
    monkeypatch.setattr(product_deleted.ProductService, "delete_product", lambda data: calls.append(("delete", data["id"])))

    payload = {"data": {"product": {"id": "p1"}}}
    product_created.handle_product_created(payload)
    product_updated.handle_product_updated(payload)
    product_deleted.handle_product_deleted(payload)

    assert ("create", "p1") in calls
    assert ("update", "p1") in calls
    assert ("delete", "p1") in calls


def test_order_failed_handler_updates_status():
    order_failed.OrderService.collection.insert_one({"id": "o1", "status": "paid"})
    order_failed.handle_order_failed({"order_id": "o1", "correlation_id": "o1"})
    updated = order_failed.OrderService.collection.find_one({"id": "o1"})
    assert updated["status"] == "failed"


def test_order_failed_handler_ignores_mismatch():
    order_failed.OrderService.collection.insert_one({"id": "o2", "status": "paid"})
    order_failed.handle_order_failed({"order_id": "o2", "correlation_id": "x"})
    data = order_failed.OrderService.collection.find_one({"id": "o2"})
    assert data["status"] == "paid"
