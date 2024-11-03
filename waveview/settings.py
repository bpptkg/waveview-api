import tempfile
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlparse

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
env.read_env(str(BASE_DIR / ".env"))

SECRET_KEY = env("SECRET_KEY")

DEBUG = env.bool("DEBUG", default=False)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

STORAGE_DIR = Path(env("STORAGE_DIR", default=str(BASE_DIR / "storage")))
if not STORAGE_DIR.exists():
    STORAGE_DIR.mkdir()

RUN_DIR = STORAGE_DIR / "run"
if not RUN_DIR.exists():
    RUN_DIR.mkdir()

DB_DIR = STORAGE_DIR / "db"
if not DB_DIR.exists():
    DB_DIR.mkdir()

PREREQUISITE_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.postgres",
    "rest_framework",
    "corsheaders",
    "drf_yasg",
    "drf_standardized_errors",
    "phonenumber_field",
    "dbbackup",
]

PROJECT_APPS = [
    "waveview.users",
    "waveview.organization",
    "waveview.volcano",
    "waveview.inventory",
    "waveview.event",
    "waveview.appconfig",
    "waveview.observation",
]

INSTALLED_APPS = PREREQUISITE_APPS + PROJECT_APPS

CORS_ORIGIN_ALLOW_ALL = True

CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

AUTH_USER_MODEL = "users.User"

SITE_ID = 1

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "corsheaders.middleware.CorsMiddleware",
]

AUTHENTICATION_BACKENDS = env.list(
    "AUTHENTICATION_BACKENDS",
    default=["django.contrib.auth.backends.ModelBackend"],
)

ROOT_URLCONF = "waveview.urls"

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

WSGI_APPLICATION = "waveview.wsgi.application"

ASGI_APPLICATION = "waveview.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DATABASE_NAME"),
        "HOST": env("DATABASE_HOST", default="127.0.0.1"),
        "USER": env("DATABASE_USER"),
        "PASSWORD": env("DATABASE_PASSWORD"),
        "PORT": env.int("DATABASE_PORT", default=5432),
    },
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.memcached.PyMemcacheCache",
        "LOCATION": env("MEMCACHED_LOCATION", default="127.0.0.1:11211"),
    }
}


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

STATIC_URL = "/static/"
STATIC_ROOT = STORAGE_DIR / "static"
if not STATIC_ROOT.exists():
    STATIC_ROOT.mkdir()
STATICFILES_DIRS = [
    BASE_DIR / "waveview" / "static",
]

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

MEDIA_URL = "/media/"
MEDIA_ROOT = STORAGE_DIR / "media"
if not MEDIA_ROOT.exists():
    MEDIA_ROOT.mkdir()

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

USE_X_FORWARDED_HOST = True

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "waveview.api.permissions.NoPermission",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FormParser",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "EXCEPTION_HANDLER": "drf_standardized_errors.handler.exception_handler",
}

JWT_ACCESS_TOKEN_LIFETIME = env.int("JWT_ACCESS_TOKEN_LIFETIME", default=60)
JWT_REFRESH_TOKEN_LIFETIME = env.int("JWT_REFRESH_TOKEN_LIFETIME", default=60 * 24 * 14)

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=JWT_ACCESS_TOKEN_LIFETIME),
    "REFRESH_TOKEN_LIFETIME": timedelta(minutes=JWT_REFRESH_TOKEN_LIFETIME),
    "UPDATE_LAST_LOGIN": True,
}

LOGGING_ROOT = STORAGE_DIR / "logs"
if not LOGGING_ROOT.exists():
    LOGGING_ROOT.mkdir()
LOG_LEVEL = env("LOG_LEVEL", default="info").upper()
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "[{asctime}] {levelname} {name} {message}",
            "style": "{",
        },
        "verbose": {
            "format": "[{asctime}] {levelname} {name} {process:d} {message}",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_false": {"()": "django.utils.log.RequireDebugFalse"},
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "handlers": {
        "console": {
            "level": LOG_LEVEL,
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "access": {
            "level": LOG_LEVEL,
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(Path(LOGGING_ROOT) / "access.log"),
            "maxBytes": 1024 * 1024 * 5,
            "backupCount": 7,
            "formatter": "verbose",
            "filters": ["require_debug_false"],
        },
        "error": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(Path(LOGGING_ROOT) / "error.log"),
            "maxBytes": 1024 * 1024 * 5,
            "backupCount": 7,
            "formatter": "verbose",
            "filters": ["require_debug_false"],
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "propagate": True,
        },
        "django.request": {
            "handlers": ["console", "error"],
            "level": "ERROR",
            "propagate": True,
        },
        "": {"handlers": ["console", "access"], "level": LOG_LEVEL},
    },
}

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=25)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=False)
EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=False)
EMAIL_TIMEOUT = env.int("EMAIL_TIMEOUT", default=None)
EMAIL_FROM_ADDRESS = env("EMAIL_FROM_ADDRESS", default="")

SWAGGER_SETTINGS = {
    "SECURITY_DEFINITIONS": {
        "Bearer": {
            "type": "JWT",
            "name": "Authorization",
            "in": "header",
            "description": (
                """
                Enter the JWT access token in the format `Bearer <token>`. This
                token should be obtained by authenticating with the API using a
                valid username and password, and should be included in the
                `Authorization` header of all requests that require
                authentication.
                
                The token should be kept secret and not shared with anyone else.
                If the token expires or is invalidated, a new token must be
                obtained by re-authenticating with the API.
                """
            ),
        }
    },
    "DEFAULT_INFO": "waveview.urls.swagger_info",
    "MULTIPART_CONTENT_TYPES": ["multipart/form-data", "image/*"],
}

REDOC_SETTINGS = {
    "SPEC_URL": ("schema-json", {"format": ".json"}),
    "LAZY_RENDERING": True,
}

REDIS_URL = env("REDIS_URL", default="redis://127.0.0.1:6379")

BROKER_URL = env("BROKER_URL", default=REDIS_URL)
BROKER_TRANSPORT_OPTIONS = {}
CELERY_RESULT_BACKEND = None
CELERY_ACCEPT_CONTENT = {"json", "pickle"}
CELERY_RESULT_SERIALIZER = "json"
CELERY_TASK_SERIALIZER = "json"
CELERY_DISABLE_RATE_LIMITS = True
CELERY_DEFAULT_QUEUE = "default"
CELERY_DEFAULT_EXCHANGE = "default"
CELERY_DEFAULT_EXCHANGE_TYPE = "direct"
CELERY_DEFAULT_ROUTING_KEY = "default"
CELERY_CREATE_MISSING_QUEUES = True
CELERYD_MAX_TASKS_PER_CHILD = 1
CELERY_IMPORTS = ()
CELERYBEAT_SCHEDULE_FILENAME = str(Path(tempfile.gettempdir()) / "waveview-celerybeat")
CELERYBEAT_SCHEDULE = {}

redis = urlparse(REDIS_URL)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [
                (redis.hostname, redis.port),
            ],
        },
    },
}

EVENT_OBSERVER_REGISTRY = [
    "waveview.contrib.bpptkg.magnitude.MagnitudeObserver",
    "waveview.contrib.bma.bulletin.BulletinObserver",
]

AMPLITUDE_CALCULATOR_REGISTRY = [
    "waveview.contrib.bpptkg.amplitude.BPPTKGAmplitudeCalculator",
]

SINOAS_WINSTON_URL = env("SINOAS_WINSTON_URL", default="http://127.0.0.1:16030")
BMA_URL = env("BMA_URL", default="https://bma.cendana15.com")
BMA_API_KEY = env("BMA_API_KEY", default="")

DBBACKUP_STORAGE = "django.core.files.storage.FileSystemStorage"
DBBACKUP_DIR = STORAGE_DIR / "dbbackup"
if not DBBACKUP_DIR.exists():
    DBBACKUP_DIR.mkdir()
DBBACKUP_STORAGE_OPTIONS = {"location": str(DBBACKUP_DIR)}
