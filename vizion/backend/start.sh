#!/bin/sh
set -e

python - <<'PY'
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.conf import settings

db = settings.DATABASES["default"]
print(
    "Database target: "
    f"user={db.get('USER')} "
    f"host={db.get('HOST')} "
    f"port={db.get('PORT')} "
    f"name={db.get('NAME')} "
    f"password_source={getattr(settings, 'DATABASE_PASSWORD_SOURCE', 'unknown')}"
)
PY

python manage.py migrate
if [ "$SEED_DEMO" = "1" ]; then
  python manage.py seed_demo
fi
python manage.py collectstatic --noinput
exec daphne -b 0.0.0.0 -p 8000 config.asgi:application
