from .base import *
DEBUG = True
REDIS_PASSWORD = 'xxxxxxxxxxxxxxxx'
REDIS_HOST = 'xxxxxxxxxxxxxxxx'
FRONTEND_URL='xxxxxxxxxxxxxxxx'
CELERY_BROKER_URL = 'redis://:{}@{}/2'.format(REDIS_PASSWORD, REDIS_HOST)