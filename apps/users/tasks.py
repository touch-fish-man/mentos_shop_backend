from apps.users.models import User
from django.conf import settings
from celery.schedules import crontab
from apps.utils.shopify_handler import SyncClient
from captcha.models import CaptchaStore
from django.utils import timezone
from celery import shared_task


@shared_task(name='update_user_level')
def update_user_level(*args, **kwargs):
    """
    定时任务，更新用户等级积分和等级，每月1号凌晨1点执行
    """
    users = User.objects.all()
    for user in users:
        user.level_points_decay()
    return 'update user level success'


@shared_task(name='update_user_level_to_shopify')
def update_user_level_to_shopify(email, level):
    """
    定时任务，更新用户等级积分和等级到shopify，每月1号凌晨1点执行
    """
    shop_url = settings.SHOPIFY_SHOP_URL
    api_key = settings.SHOPIFY_API_KEY
    api_scert = settings.SHOPIFY_API_SECRET
    private_app_password = settings.SHOPIFY_APP_KEY
    shopify_sync_client = SyncClient(shop_url, api_key, api_scert, private_app_password)
    tags = "vip" + str(level)
    shopify_sync_client.update_customer_tags_by_email(email, tags)


@shared_task(name='sync_user_to_shopify')
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


@shared_task(name='clean_captcha')
def clean_captcha():
    """
    定时任务，清理过期的验证码，每天凌晨1点执行
    """
    CaptchaStore.remove_expired()


@shared_task(name='clean_email_code')
def clean_expired_email_code():
    """
    定时任务，清理过期的邮箱验证码，每天凌晨1点执行
    """
    from apps.users.models import Code
    Code.objects.filter(created_at__lte=timezone.now() - timezone.timedelta(minutes=30)).delete()
