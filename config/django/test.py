from .base import *
DEBUG = True
REDIS_PASSWORD = 'xB8U0Q6gyrMpRYA7'
REDIS_HOST = '177.8.0.14'
FRONTEND_URL='https://test.mentosproxy.com'
CELERY_BROKER_URL = 'redis://:{}@{}/2'.format(REDIS_PASSWORD, REDIS_HOST)