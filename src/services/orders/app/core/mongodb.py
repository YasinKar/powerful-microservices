from pymongo import MongoClient
from app.core.config import settings


if settings.MONGO_USER and settings.MONGO_PASSWORD:
    client = MongoClient(
        host=settings.MONGO_HOST,
        port=settings.MONGO_PORT,
        username=settings.MONGO_USER,
        password=settings.MONGO_PASSWORD,
    )
else:
    client = MongoClient(
        host=settings.MONGO_HOST,
        port=settings.MONGO_PORT
    )

db = client[settings.MONGO_DB]
