import json

import pytest
from django.core.management import call_command

from api.models import Outbox
from events import outbox_events


class StopLoop(Exception):
    pass


@pytest.mark.django_db
def test_publish_outbox_events_marks_sent(monkeypatch):
    entry = Outbox.objects.create(
        topic="users",
        value=json.dumps({"event_type": "UserRegistered"}),
    )
    published = []

    def fake_publish_event(topic, value):
        published.append((topic, value))

    def stop_sleep(_):
        raise StopLoop()

    monkeypatch.setattr(outbox_events, "publish_event", fake_publish_event)
    monkeypatch.setattr(outbox_events.time, "sleep", stop_sleep)

    with pytest.raises(StopLoop):
        outbox_events.publish_outbox_events()

    entry.refresh_from_db()
    assert published == [("users", {"event_type": "UserRegistered"})]
    assert entry.status == "sent"
    assert entry.sent_at is not None


@pytest.mark.django_db
def test_publish_outbox_events_marks_failed_and_retries(monkeypatch):
    entry = Outbox.objects.create(
        topic="users",
        value=json.dumps({"event_type": "UserRegistered"}),
    )

    def failing_publish_event(topic, value):  # noqa: ARG001
        raise RuntimeError("kafka down")

    def stop_sleep(_):
        raise StopLoop()

    monkeypatch.setattr(outbox_events, "publish_event", failing_publish_event)
    monkeypatch.setattr(outbox_events.time, "sleep", stop_sleep)

    with pytest.raises(StopLoop):
        outbox_events.publish_outbox_events(max_retries=3)

    entry.refresh_from_db()
    assert entry.status == "dead"
    assert entry.retry_count == 3
    assert entry.last_attempt_at is not None


@pytest.mark.django_db
def test_publish_outbox_events_marks_dead_after_max_retries(monkeypatch):
    entry = Outbox.objects.create(
        topic="users",
        value=json.dumps({"event_type": "UserRegistered"}),
        status="failed",
        retry_count=4,
    )

    def failing_publish_event(topic, value):  # noqa: ARG001
        raise RuntimeError("kafka down")

    def stop_sleep(_):
        raise StopLoop()

    monkeypatch.setattr(outbox_events, "publish_event", failing_publish_event)
    monkeypatch.setattr(outbox_events.time, "sleep", stop_sleep)

    with pytest.raises(StopLoop):
        outbox_events.publish_outbox_events(max_retries=5)

    entry.refresh_from_db()
    assert entry.status == "dead"
    assert entry.retry_count == 5


def test_run_outbox_worker_command_invokes_publisher(monkeypatch):
    called = {"value": False}

    def fake_publish():
        called["value"] = True

    monkeypatch.setattr(
        "api.management.commands.run_outbox_worker.publish_outbox_events",
        fake_publish,
    )

    call_command("run_outbox_worker")

    assert called["value"] is True
