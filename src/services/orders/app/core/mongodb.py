from pymongo import MongoClient
from core.config import settings


if settings.MONGO_INITDB_ROOT_USERNAME and settings.MONGO_INITDB_ROOT_PASSWORD:
    client = MongoClient(
        host=settings.MONGO_HOST,
        port=settings.MONGO_PORT,
        username=settings.MONGO_INITDB_ROOT_USERNAME,
        password=settings.MONGO_INITDB_ROOT_PASSWORD,
        authSource="admin",
        replicaset="rs0",
    )
else:
    client = MongoClient(
        host=settings.MONGO_HOST,
        port=settings.MONGO_PORT,
        authSource="admin",
        replicaset="rs0",
    )

db = client[settings.MONGO_INITDB_DATABASE]
