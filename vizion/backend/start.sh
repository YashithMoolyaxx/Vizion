#!/bin/sh
set -e

python - <<'PY'
import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
from django.conf import settings
from django.db import connection

db = settings.DATABASES["default"]


def env_state(name):
    return "set" if os.getenv(name) else "missing"


print(
    "Database target: "
    f"user={db.get('USER')} "
    f"host={db.get('HOST')} "
    f"port={db.get('PORT')} "
    f"name={db.get('NAME')} "
    f"password_source={getattr(settings, 'DATABASE_PASSWORD_SOURCE', 'unknown')}"
)
print(
    "Database env: "
    f"MYSQL_URL={env_state('MYSQL_URL')} "
    f"MYSQL_PUBLIC_URL={env_state('MYSQL_PUBLIC_URL')} "
    f"DATABASE_URL={env_state('DATABASE_URL')} "
    f"MYSQLPASSWORD={env_state('MYSQLPASSWORD')} "
    f"MYSQL_PASSWORD={env_state('MYSQL_PASSWORD')} "
    f"MYSQL_ROOT_PASSWORD={env_state('MYSQL_ROOT_PASSWORD')}"
)

try:
    django.setup()
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
except Exception as exc:
    print(f"Database connection failed: {exc.__class__.__name__}: {exc}")
    print("Fix Render env: prefer setting MYSQL_URL to Railway's public MySQL URL, or copy MYSQLPASSWORD exactly from Railway.")
    sys.exit(1)
PY

python manage.py migrate
if [ "$SEED_DEMO" = "1" ]; then
  python manage.py seed_demo
fi
python manage.py collectstatic --noinput
exec daphne -b 0.0.0.0 -p 8000 config.asgi:application
