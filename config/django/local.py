from .base import *
DEBUG = True
REDIS_HOST = 'xxxxxxxxxxxxxxxx'
REDIS_PASSWORD = 'xxxxxxxxxxxxxxxx'
CELERY_BROKER_URL = 'redis://:{}@{}/0'.format(REDIS_PASSWORD, REDIS_HOST)