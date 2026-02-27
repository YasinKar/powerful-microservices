import json
from datetime import datetime, timezone

import pytest

from events import outbox_events
from models.outbox import Outbox


class StopLoop(Exception):
    pass


def test_publish_outbox_events_marks_sent(session, monkeypatch):
    entry = Outbox(
        topic="products",
        value=json.dumps({"event_type": "ProductCreated"}),
        created_at=datetime.now(timezone.utc),
    )
    session.add(entry)
    session.commit()
    published = []

    monkeypatch.setattr(outbox_events, "engine", session.get_bind())
    monkeypatch.setattr(outbox_events, "publish_event", lambda topic, value: published.append((topic, value)))
    monkeypatch.setattr(outbox_events.time, "sleep", lambda _: (_ for _ in ()).throw(StopLoop()))

    with pytest.raises(StopLoop):
        outbox_events.publish_outbox_events()

    session.refresh(entry)
    assert published
    assert entry.status == "sent"
    assert entry.sent_at is not None


def test_publish_outbox_events_increments_retry(session, monkeypatch):
    entry = Outbox(
        topic="products",
        value=json.dumps({"event_type": "ProductCreated"}),
        created_at=datetime.now(timezone.utc),
    )
    session.add(entry)
    session.commit()

    def failing_publish(topic, value):  # noqa: ARG001
        raise RuntimeError("down")

    monkeypatch.setattr(outbox_events, "engine", session.get_bind())
    monkeypatch.setattr(outbox_events, "publish_event", failing_publish)
    monkeypatch.setattr(outbox_events.time, "sleep", lambda _: (_ for _ in ()).throw(StopLoop()))

    with pytest.raises(StopLoop):
        outbox_events.publish_outbox_events(max_retries=2)

    session.refresh(entry)
    assert entry.retry_count == 2
    assert entry.status == "dead"
    assert entry.last_attempt_at is not None
