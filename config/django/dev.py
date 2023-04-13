from .base import *
DEBUG = True
DATABASES["default"]["HOST"] = "13.231.170.92"
DATABASES["default"]["PORT"] = "5432"
CELERY_BROKER_BACKEND = "memory"
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}