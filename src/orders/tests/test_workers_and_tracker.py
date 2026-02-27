from events import orders_tracker, outbox_worker


def test_outbox_worker_main_runs(monkeypatch):
    called = {"ok": False}

    async def fake_publish(**kwargs):
        called["ok"] = True

    monkeypatch.setattr(outbox_worker, "publish_outbox_events", fake_publish)
    outbox_worker.main()
    assert called["ok"] is True


def test_orders_tracker_has_handlers():
    assert "products" in orders_tracker.EVENT_HANDLERS
    assert "order_failures" in orders_tracker.EVENT_HANDLERS


def test_orders_tracker_main_processes_message(monkeypatch):
    processed = []

    class FakeMsg:
        def __init__(self, topic, payload):
            self._topic = topic
            self._payload = payload

        def error(self):
            return None

        def value(self):
            return self._payload

        def topic(self):
            return self._topic

    class FakeConsumer:
        def __init__(self, conf):
            self.calls = 0

        def subscribe(self, topics):
            return None

        def poll(self, timeout):
            self.calls += 1
            if self.calls == 1:
                return FakeMsg("products", b'{"event_type":"ProductCreated","data":{"product":{"id":"p1"}}}')
            raise KeyboardInterrupt()

        def commit(self, msg):
            processed.append("commit")

        def close(self):
            processed.append("close")

    monkeypatch.setattr(orders_tracker, "Consumer", FakeConsumer)
    monkeypatch.setitem(
        orders_tracker.EVENT_HANDLERS["products"],
        "ProductCreated",
        lambda data: processed.append(data["event_type"]),
    )

    orders_tracker.main()
    assert "ProductCreated" in processed
    assert "commit" in processed
    assert "close" in processed
