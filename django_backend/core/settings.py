import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

environment = os.getenv("RAILWAY_ENVIRONMENT", "development")

# Load environment file only in development
# In production (Railway), environment variables are set directly
if environment != "production":
    env_file = Path(__file__).resolve().parent.parent.parent / ".env.dev"
    load_dotenv(env_file)

MONGO_DATA_API_KEY = os.getenv("MONGO_DATA_API_KEY", "")
MONGO_DATA_API_ENDPOINT = os.getenv("MONGO_DATA_API_ENDPOINT", "")
MONGO_URI = os.getenv("MONGO_URI", "")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "")

CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID", "")
CF_NAMESPACE_ID = os.getenv("CF_NAMESPACE_ID", "")
CF_API_TOKEN = os.getenv("CF_API_TOKEN", "")

BASE_DIR = Path(__file__).resolve().parent.parent

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
DEBUG = environment != "production"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,api.tunemeld.com,tunemeld.com,www.tunemeld.com").split(
    ","
)

# Minimal environment logging
if environment == "production":
    print("Railway Production Environment")
else:
    print("Development Environment")


STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")


INSTALLED_APPS = [
    "core.apps.CoreConfig",
    "corsheaders",
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
        "pymongo": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}


CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1:5500",
    "http://localhost:3000",
    "https://www.tunemeld.com",
    "https://api.tunemeld.com",
    "https://tunemeld.com",
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

# PostgreSQL database connection string from Railway
# Format: postgresql://username:password@host:port/database_name
# Used for: persistent storage of playlist data, user sessions, and application state
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Production: Use Railway PostgreSQL database
    DATABASES = {"default": dj_database_url.parse(DATABASE_URL)}
else:
    # Development/Testing: Use file-based SQLite for Metabase integration
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "staging.db",
        }
    }
