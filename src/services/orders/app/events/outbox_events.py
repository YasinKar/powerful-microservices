import asyncio
import logging
from datetime import datetime, timezone

from core.mongodb import db
from events.kafka_producer import publish_event


logger = logging.getLogger(__name__)


outbox_collection = db["outbox"]


async def publish_outbox_events(max_retries: int = 5, backoff_seconds: int = 5):
    while True:
        # Fetch pending or retry-eligible failed entries
        pending = outbox_collection.find({
            "$or": [
                {"status": "pending"},
                {"status": "failed", "retry_count": {"$lt": max_retries}}
            ]
        }).sort("created_at", 1)

        for entry in pending:
            try:
                publish_event(topic=entry["topic"], value=entry["value"])
                outbox_collection.update_one(
                    {"id": entry["id"]},
                    {"$set": {
                        "status": "sent",
                        "sent_at": datetime.now(timezone.utc)
                    }}
                )
            except Exception as e:
                logger.error(f"Failed to publish outbox {entry['id']}: {e}")
                retry_count = entry.get("retry_count", 0) + 1
                update = {
                    "$set": {
                        "retry_count": retry_count,
                        "last_attempt_at": datetime.now(timezone.utc)
                    }
                }
                if retry_count >= max_retries:
                    update["$set"]["status"] = "dead"  # Permanently fail
                    logger.warning(f"Outbox {entry['id']} marked as failed after {retry_count} attempts")
                outbox_collection.update_one({"id": entry["id"]}, update)

        await asyncio.sleep(backoff_seconds)