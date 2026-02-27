from unittest.mock import Mock

from events import kafka_producer


def test_publish_event_calls_producer(monkeypatch):
    producer = Mock()
    monkeypatch.setattr(kafka_producer, "producer", producer)
    kafka_producer.publish_event("orders", {"event_type": "OrderPlaced"})
    producer.produce.assert_called_once()
    producer.flush.assert_called_once()


def test_publish_event_handles_error(monkeypatch):
    producer = Mock()
    producer.produce.side_effect = RuntimeError("down")
    logger = Mock()
    monkeypatch.setattr(kafka_producer, "producer", producer)
    monkeypatch.setattr(kafka_producer, "logger", logger)
    kafka_producer.publish_event("orders", {"event_type": "OrderPlaced"})
    logger.error.assert_called_once()
