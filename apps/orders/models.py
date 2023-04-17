from django.db import models
from apps.core.models import BaseModel


# Create your models here.
def gen_order_id():
    import uuid
    return str(uuid.uuid4()).replace('-', '')


class Orders(BaseModel):
    # 用户
    uid = models.CharField(max_length=255, verbose_name='用户id')
    username = models.CharField(max_length=255, verbose_name='用户名')
    # 订单号
    order_id = models.CharField(max_length=255, verbose_name='订单号', default=gen_order_id)
    # shopify订单号
    shopify_order_id = models.CharField(max_length=255, verbose_name='shopify订单号', null=True, blank=True)
    # 产品id
    product_id = models.IntegerField(verbose_name='产品id')
    # 产品名称
    product_name = models.CharField(max_length=255, verbose_name='产品名称')
    # 变体id
    variant_id = models.CharField(max_length=255,verbose_name='变体id')
    # 产品价格
    product_price = models.FloatField(verbose_name='产品价格')
    # 产品数量
    product_quantity = models.IntegerField(verbose_name='产品数量')
    # 产品总价
    product_total_price = models.FloatField(verbose_name='产品总价')
    # 产品类型
    product_type = models.IntegerField(verbose_name='产品类型')
    # 产品类型名称
    # product_type_name = models.CharField(max_length=255, verbose_name='产品类型名称')
    # 订单状态
    order_status = models.IntegerField(verbose_name='订单状态', default=0)  # 0: 未支付 1: 已支付 2: 已取消 3: 已过期, 4: 已发货
    # 支付状态 -1: 支付失败 0: 未支付 1: 支付成功
    pay_status = models.IntegerField(verbose_name='支付状态', default=0)  # 0: 未支付 1: 支付成功 2: 支付失败
    # 支付时间
    pay_time = models.DateTimeField(verbose_name='支付时间', null=True, blank=True)
    # 支付金额
    pay_amount = models.FloatField(verbose_name='支付金额', null=True, blank=True)
    # # 支付方式 后期扩展
    # pay_type = models.IntegerField(verbose_name='支付方式',default=1)
    # # 支付流水号 后期扩展
    # pay_no = models.CharField(max_length=255, verbose_name='支付流水号', null=True, blank=True)
    # # 支付备注 后期扩展
    # pay_remark = models.CharField(max_length=255, verbose_name='支付备注')
    # 支付回调时间
    # pay_callback_time = models.DateTimeField(verbose_name='支付回调时间')
    # # 支付回调状态
    # pay_callback_status = models.IntegerField(verbose_name='支付回调状态')
    # # 支付链接
    # pay_url = models.CharField(max_length=255, verbose_name='支付链接')
    # 过期时间
    expired_at = models.DateTimeField(verbose_name='过期时间', null=True, blank=True)
    # 代理数量
    proxy_num = models.IntegerField(verbose_name='代理数量', default=0)

    class Meta:
        db_table = 'orders'
        verbose_name = '订单'
        verbose_name_plural = verbose_name
