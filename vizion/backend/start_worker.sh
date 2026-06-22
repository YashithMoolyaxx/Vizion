#!/bin/sh
set -e

# Start a Celery worker. Use the same image as the web service and run this as a separate service on Render.
python manage.py migrate
if [ "$SEED_DEMO" = "1" ]; then
  python manage.py seed_demo
fi
exec celery -A config worker --loglevel=info
