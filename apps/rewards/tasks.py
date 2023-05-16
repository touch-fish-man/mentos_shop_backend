import datetime
from celery import shared_task
from apps.rewards.models import CouponCode



@shared_task(name='check_coupon_code_expired')
def check_coupon_code_expired():
    """
    定时检查db中优惠码状态，如果优惠码已使用，删除优惠码，每周检查一次
    """
    CouponCode.objects.filter(is_used=False).all().delete()
    print('check_coupon_code_expired done at %s' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
