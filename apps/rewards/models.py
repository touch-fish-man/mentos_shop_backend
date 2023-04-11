from django.db import models
from apps.core.models import BaseModel
from apps.core.validators import CustomUniqueValidator


class CouponCode(BaseModel):
    """
    优惠券码列表
    """
    CODE_TYPE_DICT = {
        1: 'discount',
        2: 'giftcard',
    }
    CODE_TYPE_DICT_REVERSE = {
        'discount': 1,
        'giftcard': 2,
    }
    code = models.CharField(max_length=32, verbose_name='优惠券码')
    discount = models.CharField(max_length=32, verbose_name='折扣') # 0.8, 0.9, 0.95, 0.98 $10, $20, $50, $100
    code_type = models.IntegerField(verbose_name='类型') # 1: 折扣码, 2: 礼品卡
    is_used = models.BooleanField(default=False, verbose_name='是否使用')
    used_at = models.DateTimeField(null=True, blank=True, verbose_name='使用时间')
    holder_uid = models.IntegerField(null=True, blank=True, verbose_name='持有者UID')
    holder_username = models.CharField(max_length=32, null=True, blank=True, verbose_name='持有者用户名')


    class Meta:
        db_table = 'coupon_code'
        verbose_name = '优惠券码'
        verbose_name_plural = verbose_name
        ordering = ('-created_at',)

    def __str__(self):
        return self.code


class PointRecord(BaseModel):
    """
    积分记录
    """
    REASON_DICT = {
        "invite": 'Invite Friend and Get Reward',
        "buy": 'Buy Product and Get Reward',
        "exchange": 'Exchange Gift Card',
        "invite_buy": 'Friend Buy Product and Get Reward',
    }
    uid = models.IntegerField(verbose_name='用户ID')
    username = models.CharField(max_length=32, verbose_name='用户名')
    point = models.IntegerField(verbose_name='积分')  # 正数为增加，负数为减少
    reason = models.CharField(max_length=32, verbose_name='原因')

    class Meta:
        db_table = 'point_record'
        verbose_name = '积分记录'
        verbose_name_plural = verbose_name
        ordering = ('-created_at',)

    def __str__(self):
        return self.username


class GiftCard(BaseModel):
    """
    礼品卡
    """
    point = models.IntegerField(verbose_name='积分')
    code = models.CharField(max_length=32, verbose_name='礼品卡码')
    mount = models.IntegerField(verbose_name='金额')
    is_exchanged = models.BooleanField(default=False, verbose_name='是否兑换')

    class Meta:
        db_table = 'gift_card'
        verbose_name = '礼品卡'
        verbose_name_plural = verbose_name
        ordering = ('-created_at',)
class LevelCode(BaseModel):
    """
    等级码
    """
    code = models.CharField(max_length=32, verbose_name='等级码')
    level = models.IntegerField(verbose_name='等级')
    discount = models.CharField(max_length=32, verbose_name='折扣') # 0.8, 0.9, 0.95, 0.98 $10, $20, $50, $100
    point = models.IntegerField(verbose_name='积分')


    class Meta:
        db_table = 'level_code'
        verbose_name = '等级码'
        verbose_name_plural = verbose_name
        ordering = ('-created_at',)

    def __str__(self):
        return self.code