from django.db import models
from apps.core.models import BaseModel
from apps.core.validators import CustomUniqueValidator

class CouponCode(BaseModel):
    """
    优惠券码
    """
    code = models.CharField(max_length=32, verbose_name='优惠券码')
    is_used = models.BooleanField(default=False, verbose_name='是否使用')
    used_at = models.DateTimeField(null=True, blank=True, verbose_name='使用时间')
    holder_uid = models.IntegerField(null=True, blank=True, verbose_name='持有者UID')
    holder_username = models.CharField(max_length=32, null=True, blank=True, verbose_name='持有者用户名')
    used_at = models.DateTimeField(null=True, blank=True, verbose_name='使用时间')
    is_used = models.BooleanField(default=False, verbose_name='是否使用')
    product_id = models.IntegerField(null=True, blank=True, verbose_name='产品ID')
    product_name = models.CharField(max_length=32, null=True, blank=True, verbose_name='产品名称')
    order_id = models.IntegerField(null=True, blank=True, verbose_name='订单ID')
    shopify_coupon_id = models.IntegerField(null=True, blank=True, verbose_name='Shopify优惠券ID')

    class Meta:
        verbose_name = '优惠券码'
        verbose_name_plural = verbose_name
        ordering = ('-created_at',)

    def __str__(self):
        return self.code
class ExchangeRecord(BaseModel):
    """
    积分兑换折扣码记录表
    """
    uid = models.IntegerField(verbose_name='用户ID')
    username = models.CharField(max_length=32, verbose_name='用户名')
    product_id = models.IntegerField(verbose_name='商品ID')
    product_name = models.CharField(max_length=32, verbose_name='商品名称')
    points = models.IntegerField(verbose_name='兑换积分')
    coupon_code = models.CharField(max_length=32, verbose_name='优惠券码')
    shopify_coupon_id = models.IntegerField(verbose_name='Shopify优惠券ID')

    class Meta:
        verbose_name = '积分兑换折扣码记录表'
        verbose_name_plural = verbose_name
        ordering = ('-created_at',)

    def __str__(self):
        return self.coupon_code
class CouponPrize(BaseModel):
    """
    优惠券奖品表
    """
    # todo 优惠券奖品表
    name = models.CharField(max_length=32, verbose_name='奖品名称')
    points = models.IntegerField(verbose_name='兑换积分')
    coupon_code = models.CharField(max_length=32, verbose_name='优惠券码')
    shopify_coupon_id = models.IntegerField(verbose_name='Shopify优惠券ID')
    is_used = models.BooleanField(default=False, verbose_name='是否使用')
    used_at = models.DateTimeField(null=True, blank=True, verbose_name='使用时间')
    holder_uid = models.IntegerField(null=True, blank=True, verbose_name='持有者UID')
    holder_username = models.CharField(max_length=32, null=True, blank=True, verbose_name='持有者用户名')
    used_at = models.DateTimeField(null=True, blank=True, verbose_name='使用时间')
    is_used = models.BooleanField(default=False, verbose_name='是否使用')
    product_id = models.IntegerField(null=True, blank=True, verbose_name='产品ID')
    product_name = models.CharField(max_length=32, null=True, blank=True, verbose_name='产品名称')
    order_id = models.IntegerField(null=True, blank=True, verbose_name='订单ID')
    shopify_coupon_id = models.IntegerField(null=True, blank=True, verbose_name='Shopify优惠券ID')

    class Meta:
        verbose_name = '优惠券奖品表'
        verbose_name_plural = verbose_name
        ordering = ('-created_at',)

    def __str__(self):
        return self.name