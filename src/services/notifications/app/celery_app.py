from celery import Celery
from kombu import Exchange, Queue

from config import settings


celery_app = Celery(
    "notifications",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)


# === Queues & Routing ===
celery_app.conf.task_queues = (
    Queue(
        settings.CELERY_QUEUE_HIGH,
        Exchange("notifications"),
        routing_key="notifications.high",
    ),
    Queue(
        settings.CELERY_QUEUE_DEFAULT,
        Exchange("notifications"),
        routing_key="notifications.default",
    ),
    Queue(
        settings.CELERY_QUEUE_LOW,
        Exchange("notifications"),
        routing_key="notifications.low",
    ),
)


# === Routing by default ===
celery_app.conf.task_default_queue = settings.CELERY_QUEUE_DEFAULT
celery_app.conf.task_default_exchange = "notifications"
celery_app.conf.task_default_routing_key = "notifications.default"


# === General Config ===
celery_app.conf.update(
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
    worker_concurrency=settings.CELERY_WORKER_CONCURRENCY,
    task_acks_late=settings.CELERY_TASK_ACKS_LATE,
    worker_prefetch_multiplier=settings.CELERY_PREFETCH_MULTIPLIER,
    task_reject_on_worker_lost=True,
    result_expires=3600,
    broker_transport_options={
        "visibility_timeout": 3600,
    },
)


celery_app.autodiscover_tasks(["tasks.email_tasks", "tasks.sms_tasks"])