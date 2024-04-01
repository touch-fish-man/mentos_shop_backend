import datetime
import ipaddress
import json
import logging
import math
import os
import threading
import time
from random import randint

from django.db.models import Sum

from apps.core.models import BaseModel
from django.db import models
from apps.utils.kaxy_handler import KaxyClient
from django.db.models.signals import post_delete, post_save
from django.dispatch.dispatcher import receiver
from django.core.cache import caches, cache
from django.forms.models import model_to_dict


# Create your models here.
class AclGroup(BaseModel):
    name = models.CharField(max_length=255, blank=True, null=True, verbose_name='ACL组名')
    description = models.CharField(max_length=255, blank=True, null=True, verbose_name='描述')
    acls = models.ManyToManyField('Acls', verbose_name='ACL', through='AclGroupThrough')
    acl_value = models.TextField(blank=True, null=True, verbose_name='ACL值')
    soft_delete = models.BooleanField(default=False, verbose_name='软删除')  # 避免外键关联删除

    class Meta:
        db_table = 'acl_group'
        verbose_name = 'ACL组'
        verbose_name_plural = 'ACL组'

    def delete(self, using=None, keep_parents=False, soft_delete=True):
        if soft_delete:
            self.soft_delete = True
            self.save()
        else:
            super().delete(using, keep_parents)

    @classmethod
    def get_acl_values(cls, acls_objs=None):
        acl_value = []
        if acls_objs:
            acls = acls_objs
        else:
            acls = cls.acls.all()
        for acl in acls:
            acl_value.extend(acl.acl_value.split('\n'))
        acl_value = list(set(acl_value))
        acl_value.sort()
        acl_value = '\n'.join(acl_value)
        return acl_value


class Acls(BaseModel):
    name = models.CharField(max_length=255, blank=True, null=True, verbose_name='ACL名')
    description = models.CharField(max_length=255, blank=True, null=True, verbose_name='描述')
    acl_value = models.TextField(blank=True, null=True, verbose_name='ACL值')
    shopify_variant_id = models.CharField(blank=True, null=True, verbose_name='Shopify变体ID', max_length=255)
    price = models.FloatField(blank=True, null=True, verbose_name='价格')

    class Meta:
        db_table = 'acls'
        verbose_name = '访问控制列表'
        verbose_name_plural = '访问控制列表'

    @classmethod
    def update_acl_cache(cls, acls=None):
        for acl in acls:
            acl_dict = model_to_dict(acl)
            cache.set('acl_cache:{}'.format(acl.id), json.dumps(acl_dict), timeout=60 * 60 * 24)

    @classmethod
    def get_acl_cache(cls, acl_id):
        acl_dict = cache.get('acl_cache:{}'.format(acl_id))
        if acl_dict:
            return json.loads(acl_dict)
        else:
            acl = cls.objects.filter(id=acl_id).first()
            if acl:
                acl_dict = model_to_dict(acl)
                cache.set('acl_cache:{}'.format(acl_id), json.dumps(acl_dict), timeout=60 * 60 * 24)
                return acl_dict

    @classmethod
    def get_acls_cache(cls):
        acls_keys = cache.keys('acl_cache:*')
        acls = {}
        for key in acls_keys:
            acl_dict = cache.get(key)
            acl_id = key.split(':')[-1]
            acls[acl_id] = json.loads(acl_dict)
        return acls


@receiver(post_save, sender=Acls)
def _mymodel_save(sender, instance, **kwargs):
    acl_dict = model_to_dict(instance)
    cache.set('acl_cache:{}'.format(instance.id), json.dumps(acl_dict))
@receiver(post_delete, sender=Acls)
def _mymodel_delete(sender, instance, **kwargs):
    cache.delete('acl_cache:{}'.format(instance.id))


class AclGroupThrough(BaseModel):
    acl_group = models.ForeignKey('AclGroup', on_delete=models.CASCADE, blank=True, null=True, verbose_name='ACL组')
    acl = models.ForeignKey('Acls', on_delete=models.CASCADE, blank=True, null=True, verbose_name='ACL')

    class Meta:
        db_table = 'acl_group_through'
        verbose_name = 'ACL组与ACL关系'
        verbose_name_plural = 'ACL组与ACL关系'
        # 不同的ACL组不能有相同的ACL组合
        unique_together = ('acl_group', 'acl')


class ServerGroup(BaseModel):
    name = models.CharField(max_length=255, blank=True, null=True, verbose_name='服务器组名')
    description = models.CharField(max_length=255, blank=True, null=True, verbose_name='描述')
    servers = models.ManyToManyField('Server', verbose_name='服务器', through='ServerGroupThrough')

    class Meta:
        db_table = 'server_group'
        verbose_name = '服务器组'
        verbose_name_plural = '服务器组'


class ServerGroupThrough(BaseModel):
    server_group = models.ForeignKey('ServerGroup', on_delete=models.CASCADE, blank=True, null=True,
                                     verbose_name='服务器组')
    server = models.ForeignKey('Server', on_delete=models.CASCADE, blank=True, null=True, verbose_name='服务器')

    class Meta:
        db_table = 'server_group_through'
        verbose_name = '服务器组与服务器关系'
        verbose_name_plural = '服务器组与服务器关系'


class Server(BaseModel):
    name = models.CharField(max_length=255, blank=True, null=True, verbose_name='服务器名')
    description = models.CharField(max_length=255, blank=True, null=True, verbose_name='描述')
    ip = models.CharField(max_length=255, blank=True, null=True, verbose_name='IP')
    cidrs = models.ManyToManyField('Cidr', verbose_name='CIDR', through='ServerCidrThrough')
    server_status = models.IntegerField(blank=True, null=True, verbose_name='服务器状态', default=1)
    faild_count = models.IntegerField(blank=True, null=True, verbose_name='失败次数', default=0)

    class Meta:
        db_table = 'server'
        verbose_name = '代理服务器'
        verbose_name_plural = '代理服务器'

    def get_cidr_info(self):
        """
        获取服务器CIDR信息
        :return:
        """
        cidr_info = []
        for cidr in self.cidrs.all():
            cidr_info.append({
                'cidr': cidr.cidr,
                'ip_count': cidr.ip_count,
                "id": cidr.id,
            })
        return cidr_info


def cidr_ip_count(cidr):
    """
    计算CIDR的IP数量
    :param cidr:
    :return:
    """
    if cidr:
        cidr = cidr.split('/')
        if len(cidr) == 2:
            ip_count = 2 ** (32 - int(cidr[1]))
            return ip_count
        else:
            return 0
    else:
        return 0


class CidrAclThrough(BaseModel):
    cidr = models.ForeignKey('Cidr', on_delete=models.CASCADE, blank=True, null=True, verbose_name='CIDR')
    acl = models.ForeignKey('Acls', on_delete=models.CASCADE, blank=True, null=True, verbose_name='ACL')

    class Meta:
        db_table = 'cidr_acl_through'
        verbose_name = 'CIDR与ACL关系'
        verbose_name_plural = 'CIDR与ACL关系'


class Cidr(BaseModel):
    cidr = models.CharField(max_length=255, blank=True, null=True, verbose_name='CIDR')
    ip_count = models.IntegerField(blank=True, null=True, verbose_name='IP数量')
    exclude_acl = models.ManyToManyField('Acls', verbose_name='可用ACL', through='CidrAclThrough')
    soft_delete = models.BooleanField(default=False, verbose_name='软删除')  # 避免外键关联删除

    class Meta:
        db_table = 'cidr'
        verbose_name = 'CIDR'
        verbose_name_plural = 'CIDR'

    def __str__(self):
        return self.cidr

    def do_oft_delete(self):
        self.soft_delete = True
        ProxyStock.objects.filter(cidr_id=self.id).update(soft_delete=True)
        self.save()


def fix_network_by_ip(cidr_str):
    """
    根据IP地址修复网段
    """
    # 获取IP地址和掩码
    ip, cidr_mask = cidr_str.split('/')
    try:
        # 获取网段
        network = ipaddress.IPv4Network((ip, cidr_mask))
    except ValueError as e:
        # 如果掩码中断开了一位，尝试修复掩码
        binary_ip = ''.join([bin(int(x))[2:].zfill(8) for x in ip.split('.')])
        # 修复掩码
        fixed_mask = binary_ip.rfind('1') + 1
        network = ipaddress.IPv4Network((ip, fixed_mask))
    return str(network)


def fix_network_by_mask(cidr_str):
    """
    根据掩码修复网段
    """
    # 获取IP地址和掩码
    ip, cidr_mask = cidr_str.split('/')
    # 获取网段
    try:
        network = ipaddress.IPv4Network((ip, cidr_mask))
    except ValueError as e:
        # 如果掩码中断开了一位，尝试修复掩码
        binary_ip = ''.join([bin(int(x))[2:].zfill(8) for x in ip.split('.')])
        fixed_binary_ip = binary_ip[:int(cidr_mask)] + '0' * (32 - int(cidr_mask))
        fixed_ip = '.'.join([str(int(fixed_binary_ip[i:i + 8], 2)) for i in range(0, 32, 8)])
        network = ipaddress.IPv4Network((fixed_ip, cidr_mask))
    return str(network)


class ServerCidrThrough(BaseModel):
    server = models.ForeignKey('Server', on_delete=models.CASCADE, blank=True, null=True, verbose_name='服务器')
    cidr = models.ForeignKey('Cidr', on_delete=models.CASCADE, blank=True, null=True, verbose_name='CIDR')

    class Meta:
        db_table = 'server_cidr_through'
        verbose_name = '服务器与CIDR关系'
        verbose_name_plural = '服务器与CIDR关系'


# 删除关系的同时删除cidr
@receiver(post_delete, sender=ServerCidrThrough)
def _mymodel_delete(sender, instance, **kwargs):
    instance.cidr.delete()


# 库存表
class ProxyStock(BaseModel):
    """
    用于网段库存共享
    """
    cidr = models.ForeignKey('Cidr', on_delete=models.CASCADE, blank=True, null=True, verbose_name='CIDR')
    acl_group = models.ForeignKey('AclGroup', on_delete=models.CASCADE, blank=True, null=True, verbose_name='ACL组')
    acl = models.ForeignKey('Acls', on_delete=models.CASCADE, blank=True, null=True, verbose_name='ACL')
    ip_stock = models.IntegerField(blank=True, null=True, verbose_name='IP数量')
    variant_id = models.IntegerField(blank=True, null=True, verbose_name='变体ID')
    cart_step = models.IntegerField(blank=True, null=True, verbose_name='购物车步长')
    cart_stock = models.IntegerField(blank=True, null=True, verbose_name='购物车库存')
    subnets = models.TextField(blank=True, null=True, verbose_name='子网')  # 用于存储所有子网
    available_subnets = models.TextField(blank=True, null=True, verbose_name='可用子网')
    soft_delete = models.BooleanField(default=False, verbose_name='软删除')  # 避免外键关联删除

    class Meta:
        db_table = 'ip_stock'
        verbose_name = 'IP库存'
        verbose_name_plural = 'IP库存'
        indexes = [
            models.Index(fields=['id', 'cidr', 'acl_group', 'cart_step'], name='ip_stock_index'),
        ]
        constraints = [
            models.UniqueConstraint(fields=['cidr', 'acl_group'], name='ip_stock_pk')
        ]

    def do_soft_delete(self):
        self.soft_delete = True
        self.save()

    def gen_subnets(self):
        """
        生成子网
        :return:
        """
        # 计算
        subnets = self.get_all_subnet(self.cidr.cidr, new_prefix=32 - int(math.log(self.cart_step, 2)))
        return subnets

    def get_next_subnet(self):
        """
        获取下一个子网
        :return:
        """
        available_subnets = self.available_subnets.split(',')
        if available_subnets:
            return available_subnets[0]

    def remove_available_subnet(self, subnet):
        """
        更新可用子网
        :return:
        """
        available_subnets = self.available_subnets.split(',')
        if available_subnets:
            available_subnets.remove(subnet)
            self.available_subnets = ','.join(available_subnets)
            self.save()

    def return_subnet(self, subnet):
        """
        归还子网
        :param subnet:
        :return:
        """
        available_subnets = self.available_subnets.split(',')
        if subnet not in available_subnets and subnet in self.subnets:
            available_subnets.append(subnet)
            available_subnets = sorted(list(set(available_subnets)))
            self.available_subnets = ','.join(available_subnets)
            self.save()

    def return_stock(self, ip_count=1):
        """
        归还库存
        :param ip_count:
        :return:
        """
        self.ip_stock += ip_count
        self.cart_stock = self.ip_stock // self.cart_step
        self.save()

    @staticmethod
    def get_all_subnet(cidr_str, new_prefix=29):
        """
        获取所有子网
        """
        # 获取IP地址和掩码
        ip, cidr_mask = cidr_str.split('/')
        # 获取网段
        network = ipaddress.IPv4Network((ip, cidr_mask))
        # 获取所有子网
        subnets = [str(subnet) for subnet in network.subnets(new_prefix=new_prefix)]
        return subnets


@receiver(post_save, sender=ProxyStock)
def proxy_stock_updated(sender, instance, **kwargs):
    """
    更新可用子网
    :param sender:
    :param instance:
    :param kwargs:
    :return:
    """
    if instance.available_subnets:
        available_subnets = instance.available_subnets.split(',')
        # 去除空字符串
        available_subnets = [x for x in available_subnets if x]
        instance.available_subnets = ','.join(available_subnets)
    for product_stock in instance.product_stocks.all():
        product_stock.update_stock()


class ProductStock(BaseModel):
    """
    产品库存表
    """
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, blank=True, null=True,
                                verbose_name='产品')
    acl = models.ForeignKey('Acls', on_delete=models.CASCADE, blank=True, null=True, verbose_name='ACL')
    option1 = models.CharField(max_length=255, blank=True, null=True, verbose_name='选项1')
    option2 = models.CharField(max_length=255, blank=True, null=True, verbose_name='选项2')
    option3 = models.CharField(max_length=255, blank=True, null=True, verbose_name='选项3')
    cart_step = models.IntegerField(blank=True, null=True, verbose_name='购物车步长')
    stock = models.IntegerField(blank=True, null=True, verbose_name='IP数量')
    server_group = models.ForeignKey('ServerGroup', on_delete=models.CASCADE, blank=True, null=True,
                                     verbose_name='服务器组')
    old_variant_id = models.IntegerField(blank=True, null=True, verbose_name='旧变体ID')
    ip_stocks = models.ManyToManyField('ProxyStock', verbose_name='IP库存', related_name='product_stocks')

    class Meta:
        db_table = 'product_stock'
        verbose_name = '产品库存'
        verbose_name_plural = '产品库存'

    def update_stock(self):
        total = self.ip_stocks.aggregate(total_stock=Sum('ip_stock'))['total_stock']
        # 如果没有ip_stocks，aggregate方法可能返回None
        if total is None:
            total = 0
        self.stock = total
        self.save()


@receiver(post_save, sender=ProductStock)
def update_product_stock_cache(sender, instance, **kwargs):
    """
    更新产品库存缓存
    :param sender:
    :param instance:
    :param kwargs:
    :return:
    """
    cache.set('product_stock_{}'.format(instance.id), instance.stock)


class Proxy(BaseModel):
    ip = models.CharField(max_length=255, blank=True, null=True, verbose_name='IP')
    username = models.CharField(max_length=255, blank=True, null=True, verbose_name='用户名')
    password = models.CharField(max_length=255, blank=True, null=True, verbose_name='密码')
    port = models.IntegerField(blank=True, null=True, verbose_name='端口')
    proxy_type = models.CharField(max_length=255, blank=True, null=True, verbose_name='类型', default='http')
    server_ip = models.CharField(max_length=255, blank=True, null=True, verbose_name='服务器IP')
    order = models.ForeignKey('orders.Orders', on_delete=models.CASCADE, blank=True, null=True, verbose_name='订单')
    local_variant_id = models.IntegerField(blank=True, null=True, verbose_name='本地变体ID')
    expired_at = models.DateTimeField(blank=True, null=True, verbose_name='过期时间')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, blank=True, null=True, verbose_name='用户')
    subnet = models.CharField(max_length=255, blank=True, null=True, verbose_name='subnet')  # 用于存储所所属子网
    ip_stock_id = models.IntegerField(blank=True, null=True, verbose_name='IP库存ID')  # 已废弃
    status = models.BooleanField(default=True, verbose_name='状态')  # 用于判断是否有效
    bing_delay = models.IntegerField(blank=True, null=True, verbose_name='bing延迟')
    amazon_delay = models.IntegerField(blank=True, null=True, verbose_name='amazon延迟')
    google_delay = models.IntegerField(blank=True, null=True, verbose_name='google延迟')
    httpbin_delay = models.IntegerField(blank=True, null=True, verbose_name='httpbin延迟')
    product_stock_ids = models.TextField(blank=True, null=True, verbose_name='产品库存ID')  # 回收库存时使用
    cidr_id = models.IntegerField(blank=True, null=True, verbose_name='CIDR ID')  # 回收库存时使用
    acl_ids = models.TextField(blank=True, null=True, verbose_name='ACL ID')  # 回收库存时使用
    old_flag = models.BooleanField(default=False, verbose_name='旧标记')  # 用于判断是否是旧的代理
    ip_stock_ids = models.CharField(blank=True, null=True, verbose_name='IP库存ID', max_length=255)  # 用于存储IP库存ID

    class Meta:
        db_table = 'proxy'
        verbose_name = '代理列表'
        verbose_name_plural = '代理列表'
        indexes = [
            models.Index(fields=['username'], name='username_index'),
            models.Index(fields=['order'], name='order_id_index'),
            models.Index(fields=['expired_at'], name='expired_at_index'),
            models.Index(fields=['ip_stock_id'], name='proxy_ip_stock_id_index'),
            models.Index(fields=['order_id'], name='proxy_order_id_index'),
            models.Index(fields=['user_id'], name='proxy_user_id_index'),
        ]

    def __str__(self):
        return f"{self.username}:{self.password}@{self.ip}:{self.port}"

    def get_proxy_str(self):
        return f"{self.username}:{self.password}@{self.ip}:{self.port}"

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.httpbin_delay == self.amazon_delay == self.bing_delay == self.google_delay == 99999:
            self.status = False
        else:
            self.status = True
        super().save(force_insert, force_update, using, update_fields)

    def judge_expired(self):
        """
        判断是否过期
        :return:
        """
        if self.expired_at:
            return self.expired_at < datetime.datetime.now()
        else:
            return False


@receiver(post_delete, sender=Proxy)
def _mymodel_delete(sender, instance, **kwargs):
    from django.core.cache import cache
    # 当最后一个代理被删除时,删除用户
    # delete_user_from_server.delay(instance.server_ip, instance.username,instance.subnet,instance.ip_stock_id)
    if Proxy.objects.filter(username=instance.username, server_ip=instance.server_ip).count() == 0:
        from .tasks import delete_user_from_server
        task_i = delete_user_from_server.apply(args=(instance.server_ip, instance.username))
    order_id = instance.order_id
    stock = ProxyStock.objects.filter(id=instance.ip_stock_id).first()
    redis_key = 'stock_opt_{}'.format(instance.ip_stock_id)
    # 归还子网,归还库存
    if stock:
        if Proxy.objects.filter(subnet=instance.subnet, ip_stock_id=stock.id).count() == 0:
            with cache.lock(redis_key):
                logging.info('归还子网{},归还库存{}'.format(instance.subnet, instance.ip_stock_id))
                stock.return_subnet(instance.subnet)
                stock.return_stock()
                # 订单表中获取本地变体id
                from apps.orders.models import Orders
                from apps.products.models import Variant
                # 更新库存
                order = Orders.objects.filter(id=order_id).first()
                variant = Variant.objects.filter(id=order.local_variant_id).first()
                if variant:
                    variant.save()


class AclTasks(BaseModel):
    task_id = models.CharField(max_length=255, blank=True, null=True, verbose_name='任务ID')
    task_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='任务名')
    task_type = models.CharField(max_length=255, blank=True, null=True, verbose_name='任务类型')
    time = models.DateTimeField(blank=True, null=True, verbose_name='时间')
    delay = models.IntegerField(blank=True, null=True, verbose_name='延迟')
    server_group = models.CharField(max_length=255, blank=True, null=True, verbose_name='服务器组')
    content = models.TextField(blank=True, null=True, verbose_name='内容')

    class Meta:
        db_table = 'acl_tasks'
        verbose_name = 'ACL任务'
        verbose_name_plural = 'ACL任务'
        managed = True
