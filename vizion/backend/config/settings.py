import os
from datetime import timedelta
from pathlib import Path
from urllib.parse import unquote, urlparse

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR.parent / ".env")
load_dotenv()


def getenv(*names, default=None):
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return default


def getenv_with_source(*names, default=None):
    for name in names:
        value = os.getenv(name)
        if value:
            return value, name
    return default, None


def mysql_config_from_url(url):
    if not url:
        return None

    parsed = urlparse(url)
    if parsed.scheme not in {"mysql", "mysql2"}:
        return None

    return {
        "ENGINE": "django.db.backends.mysql",
        "NAME": unquote(parsed.path.lstrip("/")),
        "USER": unquote(parsed.username or ""),
        "PASSWORD": unquote(parsed.password or ""),
        "HOST": parsed.hostname or "",
        "PORT": parsed.port or 3306,
        "OPTIONS": {"charset": "utf8mb4"},
    }


mysql_url, mysql_url_source = getenv_with_source("MYSQL_URL", "MYSQL_PUBLIC_URL", "DATABASE_URL")
mysql_user = getenv("MYSQL_USER", "MYSQLUSER", default="vizion")
mysql_password, mysql_password_source = getenv_with_source("MYSQLPASSWORD", "MYSQL_PASSWORD")
if not mysql_password and mysql_user == "root":
    mysql_password, mysql_password_source = getenv_with_source("MYSQL_ROOT_PASSWORD")
if not mysql_password:
    mysql_password = "vizion"
    mysql_password_source = "default"

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-secret-key")
DEBUG = os.getenv("DEBUG", "1") == "1"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "channels",
    "django_cleanup.apps.CleanupConfig",
    "users",
    "social",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": [
            "django.template.context_processors.debug",
            "django.template.context_processors.request",
            "django.contrib.auth.context_processors.auth",
            "django.contrib.messages.context_processors.messages",
        ]},
    }
]

DATABASES = {
    "default": mysql_config_from_url(mysql_url)
    or {
        "ENGINE": "django.db.backends.mysql",
        "NAME": getenv("MYSQL_DATABASE", "MYSQLDATABASE", default="vizion"),
        "USER": mysql_user,
        "PASSWORD": mysql_password,
        "HOST": getenv("MYSQL_HOST", "MYSQLHOST", default="mysql"),
        "PORT": int(getenv("MYSQL_PORT", "MYSQLPORT", default="3306")),
        "OPTIONS": {"charset": "utf8mb4"},
    }
}
DATABASE_PASSWORD_SOURCE = mysql_url_source if mysql_url else mysql_password_source

AUTH_USER_MODEL = "users.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost,http://localhost:5173,http://127.0.0.1:5173",
).split(",")

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7
SESSION_SAVE_EVERY_REQUEST = True

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [getenv("REDIS_URL", "REDIS_TLS_URL", default="redis://redis:6379/1")]},
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": getenv("REDIS_CACHE_URL", "REDIS_CACHE_TLS_URL", default="redis://redis:6379/2"),
    }
}
REDIS_FEED_URL = getenv("REDIS_FEED_URL", "REDIS_FEED_TLS_URL", default="redis://redis:6379/3")
REDIS_FEED_CELEBRITY_THRESHOLD = int(os.getenv("REDIS_FEED_CELEBRITY_THRESHOLD", "5000"))
REDIS_FEED_ACTIVE_TTL = int(os.getenv("REDIS_FEED_ACTIVE_TTL", str(60 * 60 * 24 * 7)))
REDIS_FEED_LOOKBACK_DAYS = int(os.getenv("REDIS_FEED_LOOKBACK_DAYS", "7"))
REDIS_FEED_CELEBRITY_LOOKUP_LIMIT = int(os.getenv("REDIS_FEED_CELEBRITY_LOOKUP_LIMIT", "200"))
REDIS_FEED_CACHE_LIMIT = int(os.getenv("REDIS_FEED_CACHE_LIMIT", "1000"))

CELERY_BROKER_URL = getenv("CELERY_BROKER_URL", "CELERY_BROKER_URL", "REDIS_URL", "REDIS_TLS_URL", default="redis://redis:6379/0")
CELERY_RESULT_BACKEND = getenv("CELERY_RESULT_BACKEND", "CELERY_RESULT_BACKEND", "REDIS_URL", "REDIS_TLS_URL", default="redis://redis:6379/0")
CELERY_BEAT_SCHEDULE = {
    "generate-post-insights-hourly": {
        "task": "social.tasks.generate_post_insights",
        "schedule": 3600.0,
    }
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
