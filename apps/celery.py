from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings

# 设置默认的Django设置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.django.base')

# if os.environ.get("DJANGO_ENV") == "prod":
#     os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.production")
# else:
#     os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.test")

app = Celery('mentos_shop_backend')

# 使用Django配置文件的设置
app.config_from_object('django.conf:settings', namespace='CELERY')

# 从所有已安装的应用中加载任务模块
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
