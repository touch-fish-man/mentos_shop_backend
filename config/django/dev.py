from .base import *
DEBUG = True
DATABASES["default"]["HOST"] = "13.231.170.92"
DATABASES["default"]["PASSWORD"] = "N6jvHXYf4zn8sChw"
CELERY_BROKER_BACKEND = "memory"
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}