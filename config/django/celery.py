# celery 配置
REDIS_PASSWORD = 'xB8U0Q6gyrMpRYA7'
REDIS_HOST = '177.8.0.14'
CELERY_BROKER_URL = 'redis://:{}@{}/0'.format(REDIS_PASSWORD, REDIS_HOST)
# CELERY_RESULT_BACKEND = "django-db" 要求MySQL 8
# CELERY_ACCEPT_CONTENT = ['application/json']
# CELERY_RESULT_SERIALIZER = 'json'
# CELERY_TASK_SERIALIZER = 'json'