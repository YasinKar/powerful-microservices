import logging
import json

from redis import Redis, from_url, RedisError

from core.config import settings


def get_redis_client() -> Redis:
    try:
        if settings.REDIS_URL:
            client = from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
        else:
            client = Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                encoding="utf-8",
                decode_responses=True
            )
        # Test connection
        client.ping()
        return client
    except RedisError as e:
        logging.error(f"Failed to connect to Redis: {str(e)}")
        raise


def get_cache(key: str):
    client = get_redis_client()
    value = client.get(key)
    return json.loads(value) if value else None


def set_cache(key: str, value, expire: int = 300):
    client = get_redis_client()
    client.set(key, json.dumps(value, default=str), ex=expire)


def delete_cache(key: str):
    client = get_redis_client()
    client.delete(key)    