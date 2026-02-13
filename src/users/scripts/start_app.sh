#!/bin/bash
set -e

echo "🚀 Starting Django application..."

# 3. makemigrations
echo "🛠  Running makemigrations..."
python manage.py makemigrations

# 4. migrate
echo "Running migrate..."
python manage.py migrate

# 5. Run Application with Gunicorn
echo "🌐 Starting Gunicorn..."
exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4