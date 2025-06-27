import os
from pathlib import Path

from dotenv import load_dotenv

environment = os.getenv("RAILWAY_ENVIRONMENT", "development")

# Load appropriate environment file based on environment
# Environment files are in the root directory, two levels up from settings.py
env_file_path = Path(__file__).resolve().parent.parent.parent

if environment == "development":
    load_dotenv(env_file_path / ".env.dev")
elif environment == "test":
    load_dotenv(env_file_path / ".env.test")
elif environment == "production":
    # Production should use environment variables set in Railway/hosting platform
    # We explicitly don't load .env.prod to avoid accidental exposure
    pass

MONGO_DATA_API_KEY = os.getenv("MONGO_DATA_API_KEY")
MONGO_DATA_API_ENDPOINT = os.getenv("MONGO_DATA_API_ENDPOINT")
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")

CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
CF_NAMESPACE_ID = os.getenv("CF_NAMESPACE_ID")
CF_API_TOKEN = os.getenv("CF_API_TOKEN")

BASE_DIR = Path(__file__).resolve().parent.parent

CSRF_TRUSTED_ORIGINS = [
    "https://www.tunemeld.com",
    "https://api.tunemeld.com",
    "https://tunemeld.com",
]

# SECRET_KEY is required and must be set as an environment variable
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError(
        "SECRET_KEY environment variable is required but not set. "
        "Please set it in your .env file or environment variables."
    )

DEBUG = True

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
print("ALLOWED_HOSTS:", ALLOWED_HOSTS)


STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")


INSTALLED_APPS = [
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
            "level": "INFO",
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

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Database configuration for Django tests
# Note: This app primarily uses MongoDB, but Django requires a database backend for testing
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
