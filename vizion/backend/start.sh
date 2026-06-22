#!/bin/sh
set -e

python manage.py migrate
if [ "$SEED_DEMO" = "1" ]; then
  python manage.py seed_demo
fi
exec daphne -b 0.0.0.0 -p 8000 config.asgi:application
