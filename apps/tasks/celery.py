from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings
import sys
from celery.schedules import crontab

# 设置默认的Django设置模块
if os.environ.get('DJANGO_ENV'):
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    '用户等级衰减': {
        'task': 'update_user_level',
        'schedule': crontab(hour=1, minute=0, day_of_month=1), # 每月1号凌晨1点执行
    },
    '同步用户信息至shopify': {
        'task': 'sync_user_to_shopify',
        'schedule': crontab(hour=1, minute=0), # 每天凌晨1点执行
    },
    '过期订单检查': {
        'task': 'check_order_expired',
        'schedule': 6000.0, # 每小时执行一次
    },
    '删除过期代理': {
        'task': 'delete_proxy_expired',
        'schedule': 6000.0, # 每小时执行一次
    },
    '过期订单提醒': {
        'task': 'precheck_order_expired',
        'schedule': crontab(hour=1, minute=0), # 每天凌晨1点执行
    },
    '检查优惠券过期': {
        'task': 'check_coupon_code_expired',
        'schedule': crontab(hour=1, minute=0, day_of_week=1), # 每周1凌晨1点执行
    },
    '服务器状态检查': {
        'task': 'check_server_status',
        
        'schedule': 6000.0, # 每小时执行一次
    },
    '删除超时订单': {
        'task': 'delete_timeout_order',
        'schedule': crontab(hour=1, minute=0), # 每天凌晨1点执行
    },
    '删除api请求记录': {
        'task': 'delete_api_logs',
        'schedule': crontab(hour=10, minute=0, day_of_week=1), # 每周1,10点执行
    },
    '删除过期订单': {
        'task': 'delete_expired_order',
        'schedule': crontab(hour=1, minute=30, day_of_week=1), # 每周1凌晨1点执行
    },
    '库存回收': {
        'task': 'update_product_stock',
        'schedule': 6000.0, # 每小时执行一次
    },
    '清理过期验证码': {
        'task': 'clean_captcha',
        'schedule': crontab(hour=3, minute=0), # 每天凌晨3点执行
    },
    '清理过期邮箱验证码': {
        'task': 'clean_email_code',
        'schedule': crontab(hour=2, minute=0), # 每天凌晨2点执行
    },
    '清理过期session': {
        'task': 'cleanup_sessions',
        'schedule': crontab(day_of_week=1, hour=4, minute=0), # 每周一凌晨4点执行
    },
    '代理有效性检查': {
        'task': 'check_proxy_status',
        'schedule': crontab(hour=1, minute=0), # 每四个小时执行一次
    },
    '清理代理访问日志':
    {
        'task': 'flush_access_log',
        # 每两天执行一次
        'schedule': crontab(hour=4, minute=10, day_of_week="1,3,5"),
    },
}