import json
from unittest.mock import Mock

import pytest
from redis import RedisError

from core import redis_cache
from core.config import settings


def test_get_redis_client_from_url(monkeypatch):
    client = Mock()
    client.ping.return_value = True
    monkeypatch.setattr(type(settings), "REDIS_URL", "redis://localhost:6379/0", raising=False)
    monkeypatch.setattr(redis_cache, "from_url", lambda *args, **kwargs: client)
    assert redis_cache.get_redis_client() is client


def test_get_redis_client_from_host_port(monkeypatch):
    client = Mock()
    client.ping.return_value = True
    monkeypatch.setattr(type(settings), "REDIS_URL", None, raising=False)
    monkeypatch.setattr(type(settings), "REDIS_HOST", "localhost", raising=False)
    monkeypatch.setattr(type(settings), "REDIS_PORT", 6379, raising=False)
    monkeypatch.setattr(type(settings), "REDIS_DB", 0, raising=False)
    monkeypatch.setattr(type(settings), "REDIS_PASSWORD", None, raising=False)
    monkeypatch.setattr(redis_cache, "Redis", lambda **kwargs: client)
    assert redis_cache.get_redis_client() is client


def test_get_redis_client_raises(monkeypatch):
    client = Mock()
    client.ping.side_effect = RedisError("down")
    monkeypatch.setattr(type(settings), "REDIS_URL", None, raising=False)
    monkeypatch.setattr(type(settings), "REDIS_HOST", "localhost", raising=False)
    monkeypatch.setattr(type(settings), "REDIS_PORT", 6379, raising=False)
    monkeypatch.setattr(type(settings), "REDIS_DB", 0, raising=False)
    monkeypatch.setattr(type(settings), "REDIS_PASSWORD", None, raising=False)
    monkeypatch.setattr(redis_cache, "Redis", lambda **kwargs: client)
    with pytest.raises(RedisError):
        redis_cache.get_redis_client()


def test_cache_get_set_delete(monkeypatch):
    client = Mock()
    client.get.return_value = json.dumps({"k": "v"})
    monkeypatch.setattr(redis_cache, "get_redis_client", lambda: client)

    assert redis_cache.get_cache("x") == {"k": "v"}
    redis_cache.set_cache("x", {"k": "v"}, expire=30)
    redis_cache.delete_cache("x")
    client.delete.assert_called_once_with("x")
