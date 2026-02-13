import time
import json
import logging

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from api.models import Outbox
from events.kafka_producer import publish_event 


logger = logging.getLogger(__name__)


def publish_outbox_events(max_retries: int = 5, backoff_seconds: int = 5):
    while True:
        pending = []

        with transaction.atomic():
            pending = (
                Outbox.objects
                .select_for_update(skip_locked=True)
                .filter(
                    Q(status="pending") |
                    Q(status="failed", retry_count__lt=max_retries)
                )
                .order_by("created_at")[:10]
            )

            for entry in pending:
                try:
                    publish_event(
                        topic=entry.topic,
                        value=json.loads(entry.value),
                    )

                    entry.status = "sent"
                    entry.sent_at = timezone.now()

                except Exception as e:
                    logger.error(f"Failed to publish outbox {entry.id}: {e}")

                    entry.retry_count += 1
                    entry.last_attempt_at = timezone.now()

                    if entry.retry_count >= max_retries:
                        entry.status = "dead"
                    else:
                        entry.status = "failed"

                entry.save(
                    update_fields=[
                        "status",
                        "retry_count",
                        "last_attempt_at",
                        "sent_at",
                    ]
                )

        if not pending:
            time.sleep(backoff_seconds)