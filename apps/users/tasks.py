from apps.users.models import User
from django.conf import settings
from apps import celery_app
from celery.schedules import crontab
from apps.utils.shopify_handler import SyncClient
from captcha.models import CaptchaStore
from django.utils import timezone

@celery_app.task(name='update_user_level')
def update_user_level():
    """
    定时任务，更新用户等级积分和等级，每月1号凌晨1点执行
    """
    users=User.objects.all()
    for user in users:
        user.level_points_decay()
    
def sync_user_to_shopify():
    """
    定时任务，同步用户到shopify，每天凌晨1点执行
    """
    shop_url = settings.SHOPIFY_SHOP_URL
    api_key = settings.SHOPIFY_API_KEY
    api_scert = settings.SHOPIFY_API_SECRET
    private_app_password = settings.SHOPIFY_APP_KEY
    shopify_sync_client = SyncClient(shop_url, api_key, api_scert, private_app_password)
    shopify_sync_client.sync_customers()
    
celery_app.conf.beat_schedule = {
    'update_user_level': {
        'task': 'update_user_level',
        'schedule': crontab(hour=1, minute=0, day_of_month=settings.LEVEL_POINTS_DECAY_DAY),
    },
    'sync_user_to_shopify': {
        'task': 'sync_user_to_shopify',
        'schedule': crontab(hour=1, minute=0),
    }
}