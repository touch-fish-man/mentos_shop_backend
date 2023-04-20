from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings
import sys
from celery.schedules import crontab

# 设置默认的Django设置模块
if os.environ.get('DJANGO_ENV'):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(base_dir)
    if os.path.exists(os.path.join(base_dir, 'config', 'django', os.environ.get('DJANGO_ENV') + '.py')):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django." + os.environ.get('DJANGO_ENV'))
    else:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.local")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.local")

app = Celery('mentos_shop_backend')

# 使用Django配置文件的设置
app.config_from_object('django.conf:settings', namespace='CELERY')

# 从所有已安装的应用中加载任务模块
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# 设置定时任务
app.conf.beat_schedule = {
    'update_user_level': {
        'task': 'update_user_level',
        'schedule': crontab(hour=1, minute=0, day_of_month=1), # 每月1号凌晨1点执行
    },
    'sync_user_to_shopify': {
        'task': 'sync_user_to_shopify',
        'schedule': crontab(hour=1, minute=0), # 每天凌晨1点执行
    },
    'check_order_expired': {
        'task': 'check_order_expired',
        'schedule': crontab(hour=1, minute=0), # 每天凌晨1点执行
    },
    'delete_proxy_expired': {
        'task': 'delete_proxy_expired',
        'schedule': crontab(hour=1, minute=0), # 每天凌晨1点执行
    },
    'precheck_order_expired': {
        'task': 'precheck_order_expired',
        'schedule': crontab(hour=1, minute=0), # 每天凌晨1点执行
    },
    'check_coupon_code_expired': {
        'task': 'check_coupon_code_expired',
        'schedule': crontab(hour=1, minute=0, day_of_week=1), # 每周1凌晨1点执行
    },
    'check_server_status': {
        'task': 'check_server_status',
        
        'schedule': 600.0, # 每十分钟执行一次
    },
}