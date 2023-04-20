from .base import *
DEBUG = True
DATABASES["default"]["HOST"] = "13.231.170.92"
DATABASES["default"]["PORT"] = "5432"
REDIS_HOST = '13.231.170.92'
REDIS_PASSWORD = 'xB8U0Q6gyrMpRYA7'
CELERY_BROKER_URL = 'redis://:{}@{}/4'.format(REDIS_PASSWORD, REDIS_HOST)