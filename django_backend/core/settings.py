import logging
import os
import zoneinfo
from datetime import datetime, timezone
from pathlib import Path
from typing import Final

import dj_database_url
from dotenv import load_dotenv


class ETFormatter(logging.Formatter):
    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        et_tz = zoneinfo.ZoneInfo("America/New_York")
        dt.astimezone(et_tz)
        return dt.strftime("%I:%M:%S%p ET").replace(" 0", " ")


DEV: Final = "dev"
PROD: Final = "prod"


def get_environment() -> str:
    if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("GITHUB_ACTIONS"):
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

BASE_DIR = Path(__file__).resolve().parent.parent

PROD_API_BASE_URL = "https://api.tunemeld.com"
DEV_API_BASE_URL = "http://localhost:8000"

INTERNAL_API_BASE_URL = DEV_API_BASE_URL if ENVIRONMENT == DEV else PROD_API_BASE_URL

CSRF_TRUSTED_ORIGINS = [
    "https://www.tunemeld.com",
    "https://api.tunemeld.com",
    "https://tunemeld.com",
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

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,api.tunemeld.com,tunemeld.com,www.tunemeld.com").split(
    ","
)

if ENVIRONMENT == PROD:
    print("Railway Production Environment")
else:
    print("Development Environment")


STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")


INSTALLED_APPS = [
    "core.apps.CoreConfig",
    "corsheaders",
    "graphene_django",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_distill",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s [%(name)s:%(lineno)d] %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
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

CACHES = {
    "default": {
        "BACKEND": "core.cache.Cache",
        "LOCATION": f"tunemeld-cache-{ENVIRONMENT}",
        "TIMEOUT": CACHE_TIMEOUT,
        "OPTIONS": {
            "MAX_ENTRIES": 1000,
        },
    }
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
]
ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

if ENVIRONMENT == DEV:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "staging.db",
        }
    }
else:
    # Production: Use Railway PostgreSQL database
    DATABASES = {"default": dj_database_url.parse(os.getenv("DATABASE_URL"))}

USE_POSTGRES_API = ENVIRONMENT == DEV

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

GRAPHENE = {"SCHEMA": "core.graphql.schema.schema"}
