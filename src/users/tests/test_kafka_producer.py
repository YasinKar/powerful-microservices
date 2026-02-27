from unittest.mock import Mock

from events import kafka_producer


def test_publish_event_produces_and_flushes(monkeypatch):
    producer = Mock()
    monkeypatch.setattr(kafka_producer, "producer", producer)

    kafka_producer.publish_event("users", {"event_type": "UserRegistered"})

    producer.produce.assert_called_once()
    producer.flush.assert_called_once()


def test_publish_event_handles_producer_errors(monkeypatch):
    producer = Mock()
    producer.produce.side_effect = RuntimeError("boom")
    logger = Mock()

    monkeypatch.setattr(kafka_producer, "producer", producer)
    monkeypatch.setattr(kafka_producer, "logger", logger)

    kafka_producer.publish_event("users", {"event_type": "UserRegistered"})

    logger.error.assert_called_once()
