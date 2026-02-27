import json
from unittest.mock import Mock

import pytest
from redis import RedisError

from core import redis_cache


def test_get_redis_client_uses_url(monkeypatch):
    client = Mock()
    client.ping.return_value = True
    monkeypatch.setattr(redis_cache.settings, "REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setattr(redis_cache, "from_url", lambda *args, **kwargs: client)

    result = redis_cache.get_redis_client()

    assert result is client
    client.ping.assert_called_once()


def test_get_redis_client_uses_host_port(monkeypatch):
    client = Mock()
    client.ping.return_value = True
    monkeypatch.setattr(redis_cache.settings, "REDIS_URL", None)
    monkeypatch.setattr(redis_cache, "Redis", lambda **kwargs: client)

    result = redis_cache.get_redis_client()

    assert result is client
    client.ping.assert_called_once()


def test_get_redis_client_raises_on_connection_error(monkeypatch):
    bad_client = Mock()
    bad_client.ping.side_effect = RedisError("down")
    monkeypatch.setattr(redis_cache.settings, "REDIS_URL", None)
    monkeypatch.setattr(redis_cache, "Redis", lambda **kwargs: bad_client)

    with pytest.raises(RedisError):
        redis_cache.get_redis_client()


def test_get_cache_parses_json(monkeypatch):
    client = Mock()
    client.get.return_value = json.dumps({"id": "1"})
    monkeypatch.setattr(redis_cache, "get_redis_client", lambda: client)

    assert redis_cache.get_cache("k") == {"id": "1"}


def test_set_cache_serializes_value(monkeypatch):
    client = Mock()
    monkeypatch.setattr(redis_cache, "get_redis_client", lambda: client)

    redis_cache.set_cache("k", {"id": "1"}, expire=90)

    client.set.assert_called_once()


def test_delete_cache_deletes_key(monkeypatch):
    client = Mock()
    monkeypatch.setattr(redis_cache, "get_redis_client", lambda: client)

    redis_cache.delete_cache("k")

    client.delete.assert_called_once_with("k")
