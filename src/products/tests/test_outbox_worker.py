from events import outbox_worker


def test_outbox_worker_main_invokes_publisher(monkeypatch):
    called = {"ok": False}

    def fake_publish():
        called["ok"] = True

    monkeypatch.setattr(outbox_worker, "publish_outbox_events", fake_publish)
    outbox_worker.main()

    assert called["ok"] is True
