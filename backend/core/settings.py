import logging
import os
import sys
import zoneinfo
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

import dj_database_url
from dotenv import load_dotenv


class ETFormatter(logging.Formatter):
    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        dt = datetime.fromtimestamp(record.created, tz=UTC)
        et_tz = zoneinfo.ZoneInfo("America/New_York")
        et_dt = dt.astimezone(et_tz)
        return et_dt.strftime("%Y-%m-%d %I:%M:%S%p ET").replace(" 0", " ")


DEV: Final = "dev"
PROD: Final = "prod"


def get_environment() -> str:
    if os.getenv("GITHUB_ACTIONS") or os.getenv("VERCEL"):
        return PROD
    return DEV


ENVIRONMENT = get_environment()

# In dev, load environment variables from .env.dev file
if ENVIRONMENT == DEV:
    env_file = Path(__file__).resolve().parent.parent.parent / ".env.dev"
    load_dotenv(env_file)


CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID", "")
CF_NAMESPACE_ID = os.getenv("CF_NAMESPACE_ID", "")
CF_API_TOKEN = os.getenv("CF_API_TOKEN", "")

MAX_WORKERS: Final = 4

BASE_DIR = Path(__file__).resolve().parent.parent

PROD_API_BASE_URL = "https://api.tunemeld.com"
DEV_API_BASE_URL = "http://localhost:8000"

INTERNAL_API_BASE_URL = DEV_API_BASE_URL if ENVIRONMENT == DEV else PROD_API_BASE_URL

# CloudFlare Worker URLs
PROD_WORKER_BASE_URL = "https://tunemeld-worker.eli.workers.dev"
DEV_WORKER_BASE_URL = "https://tunemeld-worker-dev.eli.workers.dev"

WORKER_BASE_URL = DEV_WORKER_BASE_URL if ENVIRONMENT == DEV else PROD_WORKER_BASE_URL

CSRF_TRUSTED_ORIGINS = [
    "https://www.tunemeld.com",
    "https://api.tunemeld.com",
    "https://tunemeld.com",
    "https://tunemeld.vercel.app",
    "https://tunemeld-kx0bo9451-elis-projects-3efca02e.vercel.app",
]


# Django secret key for cryptographic signing, sessions, CSRF protection, and password hashing
# CRITICAL: Must be kept secret and unique per deployment environment
# Used for: session security, CSRF tokens, password reset tokens, and cookie signing
SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-!^u31q!@ui68(aook0g4w@jw*ei=%bbx1d8em_bm8hxm+6te#0",  # Development fallback only
)

# Set DEBUG based on environment
DEBUG = ENVIRONMENT == DEV

ALLOWED_HOSTS = os.getenv(
    "ALLOWED_HOSTS", "localhost,127.0.0.1,api.tunemeld.com,tunemeld.com,www.tunemeld.com,.vercel.app"
).split(",")

logger = logging.getLogger(__name__)
if ENVIRONMENT == PROD:
    logger.info("Production Environment")
else:
    logger.info("Development Environment")


# Static files now served by Cloudflare Pages
# STATIC_URL = "/static/"
# STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
# STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]


INSTALLED_APPS = [
    "core.apps.CoreConfig",
    "corsheaders",
]

# Add django_distill only in development (for static site generation)
if ENVIRONMENT == DEV:
    INSTALLED_APPS.append("django_distill")

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s [%(name)s:%(lineno)d] %(message)s",
        },
        "et_formatter": {
            "()": "core.settings.ETFormatter",
            "format": "%(levelname)s %(asctime)s [%(name)s:%(lineno)d] %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "et_formatter",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console"],
            "level": "DEBUG" if DEBUG else "INFO",
        },
        "django.request": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.server": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        # Quiet noisy third-party loggers
        "WDM": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "urllib3.connectionpool": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "selenium": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "webdriver_manager": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}


# Cache timeout - only cleared manually or by playlist ETL
CACHE_TIMEOUT = 86400 * 7  # 7 days

# Cache Architecture:
# - default: CloudflareKV for Django/ETL operations (raw API data, management commands)
# - redis: Vercel Redis for GraphQL query results (replaces local memory cache)

is_runserver = len(sys.argv) > 1 and sys.argv[1] == "runserver"
is_dev_mgmt_command = ENVIRONMENT == DEV and not is_runserver

# Redis configuration for Vercel Redis

# Redis configuration for Vercel Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/1")

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "tunemeld-cache",
        "TIMEOUT": CACHE_TIMEOUT,
        "OPTIONS": {
            "MAX_ENTRIES": 1000,
        },
    },
    "redis": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "TIMEOUT": CACHE_TIMEOUT,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_PREFIX": f"tunemeld-{ENVIRONMENT}",
        "VERSION": 1,
    },
}

# Cache middleware settings
CACHE_MIDDLEWARE_ALIAS = "default"
CACHE_MIDDLEWARE_SECONDS = CACHE_TIMEOUT
CACHE_MIDDLEWARE_KEY_PREFIX = f"tunemeld-{ENVIRONMENT}"

CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1:5500",
    "http://localhost:3000",
    "http://localhost:8080",
    "https://tunemeld.com",
    "https://www.tunemeld.com",
    "https://api.tunemeld.com",
    "https://tunemeld.vercel.app",
    "https://tunemeld-kx0bo9451-elis-projects-3efca02e.vercel.app",
]

# Additional CORS settings for local development
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "core" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise ValueError("DATABASE_URL environment variable is required")
DATABASES = {"default": dj_database_url.parse(database_url)}

USE_POSTGRES_API = ENVIRONMENT == DEV

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
