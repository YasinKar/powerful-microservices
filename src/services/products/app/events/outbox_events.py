import time
import logging
import json
from datetime import datetime, timezone
from sqlalchemy import or_, select
from sqlmodel import Session

from core.db import engine
from events.kafka_producer import publish_event
from models.outbox import Outbox


logger = logging.getLogger(__name__)


def publish_outbox_events(max_retries: int = 5, backoff_seconds: int = 5):
    while True:
        with Session(engine) as session:
            statement = (
                select(Outbox)
                .where(
                    or_(
                        Outbox.status == "pending",
                        (Outbox.status == "failed") & (Outbox.retry_count < max_retries)
                    )
                )
                .order_by(Outbox.created_at)
                .limit(10)
                .with_for_update(skip_locked=True) 
            )
            
            pending = session.exec(statement).scalars().all()

            for entry in pending:
                try:
                    publish_event(topic=entry.topic, value=json.loads(entry.value))
                    entry.status = "sent"
                    entry.sent_at = datetime.now(timezone.utc)
                except Exception as e:
                    logger.error(f"Failed to publish outbox {entry.id}: {e}")
                    entry.retry_count += 1
                    entry.last_attempt_at = datetime.now(timezone.utc)
                    if entry.retry_count >= max_retries:
                        entry.status = "dead"
            
                session.add(entry)

            session.commit()
        
        # Avoid busy loop if empty
        if not pending:
            time.sleep(backoff_seconds)