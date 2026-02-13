from django.core.management.base import BaseCommand
from events.outbox_events import publish_outbox_events


class Command(BaseCommand):
    help = "Run Outbox Publisher Worker"

    def handle(self, *args, **options):
        publish_outbox_events()