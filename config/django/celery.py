# celery 配置
REDIS_PASSWORD = 'xB8U0Q6gyrMpRYA7'
REDIS_HOST = '13.231.170.92'
# celery beat配置
# CELERY_ENABLE_UTC = False
CELERY_TIMEZONE = "UTC"
DJANGO_CELERY_BEAT_TZ_AWARE = True
CELERY_BEAT_SCHEDULER = 'django-celery-beat.schedulers.DatabaseScheduler'
# celery 的启动工作数量设置
CELERY_WORKER_CONCURRENCY = 10
# 任务预取功能，会尽量多拿 n 个，以保证获取的通讯成本可以压缩。
CELERYD_PREFETCH_MULTIPLIER = 20
# 有些情况下可以防止死锁
CELERYD_FORCE_EXECV = True
# celery 的 worker 执行多少个任务后进行重启操作
CELERY_WORKER_MAX_TASKS_PER_CHILD = 100
CELERY_DISABLE_RATE_LIMITS = True
# 设置代理人broker
CELERY_BROKER_URL = 'redis://:{}@{}/0'.format(REDIS_PASSWORD, REDIS_HOST)
# 指定 Backend
CELERY_RESULT_BACKEND = "django-db"
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_SERIALIZER = 'json'
