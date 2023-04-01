from django.db import models
from apps.core.models import BaseModel


# Create your models here.
def gen_order_id():
    import uuid
    return str(uuid.uuid4()).replace('-', '')


class Orders(BaseModel):
    # 用户
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name='用户')
    # 订单号
    order_id = models.CharField(max_length=255, verbose_name='订单号', default=gen_order_id)
    # shopify订单号
    shopify_order_id = models.CharField(max_length=255, verbose_name='shopify订单号')
    # 产品id
    product_id = models.IntegerField(verbose_name='产品id')
    # 产品名称
    product_name = models.CharField(max_length=255, verbose_name='产品名称')
    # 产品价格
    product_price = models.FloatField(verbose_name='产品价格')
    # 产品数量
    product_num = models.IntegerField(verbose_name='产品数量')
    # 产品总价
    product_total_price = models.FloatField(verbose_name='产品总价')
    # 产品类型
    product_type = models.IntegerField(verbose_name='产品类型')
    # 支付链接
    pay_url = models.CharField(max_length=255, verbose_name='支付链接')
    # 订单状态
    order_status = models.IntegerField(verbose_name='订单状态')
    # 支付方式
    pay_type = models.IntegerField(verbose_name='支付方式')
    # 支付状态
    pay_status = models.IntegerField(verbose_name='支付状态')
    # 支付时间
    pay_time = models.DateTimeField(verbose_name='支付时间')
    # 支付金额
    pay_amount = models.FloatField(verbose_name='支付金额')
    # 支付流水号
    pay_no = models.CharField(max_length=255, verbose_name='支付流水号')
    # 支付备注
    pay_remark = models.CharField(max_length=255, verbose_name='支付备注')
    # shopifywebhook 通知订单状态 或者api轮询订单状态
    # 支付回调时间
    pay_callback_time = models.DateTimeField(verbose_name='支付回调时间')
    # 支付回调状态
    pay_callback_status = models.IntegerField(verbose_name='支付回调状态')
    # 过期时间
    expired_at = models.DateTimeField(verbose_name='过期时间')
    # 代理数量
    proxy_num = models.IntegerField(verbose_name='代理数量')

    class Meta:
        db_table = 'orders'
        verbose_name = '订单'
        verbose_name_plural = verbose_name
