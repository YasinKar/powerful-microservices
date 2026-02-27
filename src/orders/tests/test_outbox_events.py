import asyncio
from datetime import datetime, timezone

import pytest

from events import outbox_events


class StopLoop(Exception):
    pass


def test_publish_outbox_marks_sent(monkeypatch):
    outbox_events.outbox_collection.insert_one(
        {
            "id": "ob1",
            "topic": "orders",
            "value": {"event_type": "OrderPlaced"},
            "created_at": datetime.now(timezone.utc),
            "status": "pending",
            "retry_count": 0,
        }
    )
    published = []
    monkeypatch.setattr(outbox_events, "publish_event", lambda topic, value: published.append((topic, value)))
    monkeypatch.setattr(outbox_events.asyncio, "sleep", lambda s: (_ for _ in ()).throw(StopLoop()))

    with pytest.raises(StopLoop):
        asyncio.run(outbox_events.publish_outbox_events(max_retries=2, backoff_seconds=0))

    data = outbox_events.outbox_collection.find_one({"id": "ob1"})
    assert published
    assert data["status"] == "sent"


def test_publish_outbox_marks_dead_after_retries(monkeypatch):
    outbox_events.outbox_collection.insert_one(
        {
            "id": "ob2",
            "topic": "orders",
            "value": {"event_type": "OrderPlaced"},
            "created_at": datetime.now(timezone.utc),
            "status": "pending",
            "retry_count": 0,
        }
    )

    def failing_publish(topic, value):  # noqa: ARG001
        raise RuntimeError("kafka down")

    monkeypatch.setattr(outbox_events, "publish_event", failing_publish)
    monkeypatch.setattr(outbox_events.asyncio, "sleep", lambda s: (_ for _ in ()).throw(StopLoop()))

    with pytest.raises(StopLoop):
        asyncio.run(outbox_events.publish_outbox_events(max_retries=1, backoff_seconds=0))

    data = outbox_events.outbox_collection.find_one({"id": "ob2"})
    assert data["status"] == "dead"
