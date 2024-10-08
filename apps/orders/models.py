import datetime

from django.db import models
from apps.core.models import BaseModel
from apps.products.models import Variant
import rich
from rich.console import Console
from rich.table import Table
from rich import box
from rich.align import Align
from rich.panel import Panel
import pytz
console = Console()


# Create your models here.
def gen_order_id():
    import uuid
    return str(uuid.uuid4()).replace('-', '')


class Orders(BaseModel):
    PAY_STATUS = {0: "未支付", 1: "支付成功", 2: "支付失败"}
    ORDER_STATUS = {0: "未支付", 1: "已支付", 2: "已取消", 3: "已过期", 4: "已发货", 5: "部分发货"}
    PAY_STATUS_REVERSE = {v: int(k) for k, v in PAY_STATUS.items()}
    ORDER_STATUS_REVERSE = {v: int(k) for k, v in ORDER_STATUS.items()}
    # 用户
    uid = models.CharField(max_length=255, verbose_name='用户id')
    username = models.CharField(max_length=255, verbose_name='用户名')
    # 订单号
    order_id = models.CharField(max_length=255, verbose_name='订单号', default=gen_order_id)
    # shopify订单id
    shopify_order_id = models.CharField(max_length=255, verbose_name='shopify订单id', null=True, blank=True)
    # shopify订单号
    shopify_order_number = models.CharField(max_length=255, verbose_name='shopify订单号', null=True, blank=True)
    # 产品id
    product = models.ForeignKey('products.Product', on_delete=models.PROTECT, verbose_name='产品', related_name='orders')
    # 产品名称
    product_name = models.CharField(max_length=255, verbose_name='产品名称')
    # 变体id
    variant_id = models.CharField(max_length=255, verbose_name='变体id')  # shopify的变体id
    local_variant_id = models.IntegerField(verbose_name='本地变体id')  # 本地的变体id

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
    order_status = models.IntegerField(verbose_name='订单状态', default=0, choices=ORDER_STATUS.items())
    # 支付状态 -1: 支付失败 0: 未支付 1: 支付成功
    pay_status = models.IntegerField(verbose_name='支付状态', default=0, choices=PAY_STATUS.items())
    # 支付时间
    pay_time = models.DateTimeField(verbose_name='支付时间', null=True, blank=True)
    # 支付金额
    pay_amount = models.FloatField(verbose_name='支付金额', null=True, blank=True, default=0.0)
    renew_status = models.IntegerField(verbose_name='续费状态', default=0)
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
    # 支付链接 用于支付和续费
    checkout_url = models.TextField(verbose_name='支付链接', null=True, blank=True)
    # 过期时间
    expired_at = models.DateTimeField(verbose_name='过期时间', null=True, blank=True)
    # 代理数量
    proxy_num = models.IntegerField(verbose_name='代理数量', default=0)
    # 代理时间
    proxy_time = models.IntegerField(default=30, verbose_name='代理时间')
    delivery_status = models.IntegerField(verbose_name='发货状态', default=0)
    delivery_num = models.IntegerField(verbose_name='发货数量', default=0)
    reset_time = models.DateTimeField(verbose_name='重置时间', null=True, blank=True)
    # 变体名称
    variant_name = models.CharField(max_length=255, verbose_name='变体名称', null=True, blank=True)
    option1 = models.CharField(max_length=255, verbose_name='选项1', null=True, blank=True)
    option2 = models.CharField(max_length=255, verbose_name='选项2', null=True, blank=True)
    option3 = models.CharField(max_length=255, verbose_name='选项3', null=True, blank=True)
    acl_selected = models.CharField(verbose_name='acl选项', null=True, blank=True, max_length=255)
    old_flag = models.IntegerField(verbose_name='老订单标记', default=0)
    fail_reason = models.CharField(max_length=255, verbose_name='失败原因', null=True, blank=True)
    archive= models.IntegerField(verbose_name='归档', default=0)

    class Meta:
        db_table = 'orders'
        verbose_name = '订单'
        verbose_name_plural = verbose_name
        ordering = ['-id']

    def get_variant_name_value(self):
        try:
            return Variant.objects.get(id=self.local_variant_id).variant_name
        except:
            return ''

    @staticmethod
    def get_vaild_orders(delivery_status=1):
        utc_now = datetime.datetime.now(pytz.utc)
        return Orders.objects.filter(order_status__in=[0, 1, 4], expired_at__gt=utc_now,
                                     delivery_status=delivery_status).all()

    @staticmethod
    def get_vaild_orders_by_uid(uid, delivery_status=1):

        utc_now = datetime.datetime.now(pytz.utc)
        return Orders.objects.filter(uid=uid, order_status__in=[0, 1, 4], expired_at__gt=utc_now,
                                     delivery_status=delivery_status).all()

    def get_proxies(self):
        from apps.proxy_server.models import Proxy
        proxy = Proxy.objects.filter(order_id=self.id).all()
        return proxy

    def get_proxies_failed(self):
        from apps.proxy_server.models import Proxy
        failed_cnt = Proxy.objects.filter(order_id=self.id, status=0).count()
        return failed_cnt

    def pretty_print(self, print_dict={}):
        table = Table(title="订单详情", box=box.SIMPLE)
        table.add_column("用户名", justify="center", style="cyan", no_wrap=True)
        table.add_column("订单号", justify="center", style="cyan", no_wrap=True)
        table.add_column("产品名称", justify="center", style="cyan", no_wrap=True)
        table.add_column("产品数量", justify="center", style="cyan", no_wrap=True)
        table.add_column("产品总价", justify="center", style="cyan", no_wrap=True)
        table.add_column("订单状态", justify="center", style="cyan", no_wrap=True)
        table.add_column("支付状态", justify="center", style="cyan", no_wrap=True)
        table.add_column("到期时间", justify="center", style="cyan", no_wrap=True)
        table.add_column("发货数量", justify="center", style="cyan", no_wrap=True)
        if not print_dict:
            table.add_row(
                self.username,
                self.order_id,
                self.product_name,
                str(self.product_quantity),
                str(self.product_total_price),
                self.ORDER_STATUS[self.order_status],
                self.PAY_STATUS[self.pay_status],
                self.expired_at.strftime("%Y-%m-%d %H:%M:%S"),
                str(self.delivery_num),
            )
        else:
            v_list = []
            for k,v in print_dict.items():
                table.add_column(k, justify="center", style="cyan", no_wrap=True)
                v_list.append(str(v))
            table.add_row(
                self.username,
                self.order_id,
                self.product_name,
                str(self.product_quantity),
                str(self.product_total_price),
                self.ORDER_STATUS[self.order_status],
                self.PAY_STATUS[self.pay_status],
                self.expired_at.strftime("%Y-%m-%d %H:%M:%S"),
                str(self.delivery_num),
                *v_list
            )

        console.print(table)
