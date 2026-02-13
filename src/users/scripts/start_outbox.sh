#!/bin/bash
set -e

echo "🚀 Starting Outbox events publisher..."

exec python manage.py run_outbox_worker