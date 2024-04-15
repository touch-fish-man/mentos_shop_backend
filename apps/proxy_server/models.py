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
from django.db.models.signals import post_delete, post_save, m2m_changed, pre_save
from django.dispatch.dispatcher import receiver
from django.core.cache import caches, cache
from django.forms.models import model_to_dict
from django.core.serializers.json import DjangoJSONEncoder


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
        redis_client = cache.client.get_client()
        for acl in acls:
            acl_dict = model_to_dict(acl)
            redis_client.hset('acl_cache', acl.id, json.dumps(acl_dict, cls=DjangoJSONEncoder))
            redis_client.expire('acl_cache', 60 * 60 * 8)

    @classmethod
    def get_acl_cache(cls, acl_id):
        redis_client = cache.client.get_client()
        acl_dict = redis_client.hget('acl_cache', acl_id)
        if acl_dict:
            return json.loads(acl_dict)
        else:
            acl = cls.objects.filter(id=acl_id).first()
            if acl:
                acl_dict = model_to_dict(acl)
                redis_client.hset('acl_cache', acl_id, json.dumps(acl_dict, cls=DjangoJSONEncoder))
                redis_client.expire('acl_cache', 60 * 60 * 8)
                return acl_dict

    @classmethod
    def get_acls_cache(cls):
        redis_client = cache.client.get_client()
        acls_info = redis_client.hgetall('acl_cache')
        acls = {}
        for acl_id, acl_info in acls_info.items():
            acls[acl_id] = json.loads(acl_info)
        return acls


@receiver(post_save, sender=Acls)
def _mymodel_save(sender, instance, **kwargs):
    acl_dict = model_to_dict(instance)
    redis_client = cache.client.get_client()
    from apps.proxy_server.tasks import update_product_acl
    update_product_acl.delay([instance.id])
    redis_client.hset('acl_cache', instance.id, json.dumps(acl_dict, cls=DjangoJSONEncoder))


@receiver(post_delete, sender=Acls)
def _mymodel_delete(sender, instance, **kwargs):
    redis_client = cache.client.get_client()
    redis_client.hdel('acl_cache', instance.id)


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
    servers = models.ManyToManyField('Server', verbose_name='服务器', through='ServerGroupThrough',
                                     related_name='server_groups')

    class Meta:
        db_table = 'server_group'
        verbose_name = '服务器组'
        verbose_name_plural = '服务器组'

    def get_cidrs(self):
        cidrs = []
        for server in self.servers.all():
            for cidr in server.cidrs.all():
                cidrs.append(cidr)
        return cidrs


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
    exclude_label = models.BooleanField(default=False, verbose_name='排除标签')  # 用于排除标签

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

    def reset_stock(self):
        self.available_subnets = self.subnets
        self.ip_stock = sum([ipaddress.ip_network(x).num_addresses for x in self.available_subnets.split(',') if x])
        self.cart_stock = self.ip_stock // self.cart_step
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

    def remove_available_subnet(self, subnets):
        """
        更新可用子网
        :return:
        """
        if isinstance(subnets, str):
            subnets = [subnets]
        available_subnets = self.available_subnets.split(',')
        if available_subnets:
            for subnet in subnets:
                if subnet in available_subnets:
                    available_subnets.remove(subnet)
                    available_subnets = list(set(available_subnets))
                    available_subnets.sort(key=lambda x: int(ipaddress.ip_network(x).network_address))
                    self.available_subnets = ','.join(available_subnets)
        self.save()

    def return_subnet(self, subnet):
        """
        归还子网
        :param subnet:
        :return:
        """
        available_subnets = self.available_subnets.split(',')
        if "" in available_subnets:
            available_subnets.remove("")
        if subnet not in available_subnets and subnet in self.subnets:
            available_subnets.append(subnet)
            available_subnets = list(set(available_subnets))
            available_subnets.sort(key=lambda x: int(ipaddress.ip_network(x).network_address))
            self.available_subnets = ','.join(available_subnets)
            self.ip_stock = sum([ipaddress.ip_network(x).num_addresses for x in available_subnets if x])
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
    stock = models.IntegerField(blank=True, null=True, verbose_name='IP数量', default=0)
    server_group = models.ForeignKey('ServerGroup', on_delete=models.CASCADE, blank=True, null=True,
                                     verbose_name='服务器组', related_name='product_stocks')
    variant = models.ForeignKey('products.Variant', on_delete=models.CASCADE, blank=True, null=True,
                                verbose_name='变体ID', related_name='product_stocks')

    class Meta:
        db_table = 'product_stock'
        verbose_name = '产品库存'
        verbose_name_plural = '产品库存'

    def count_stock(self):
        cidr_ids = self.server_group.get_cidrs()
        acl_id = self.acl.id
        step = self.cart_step
        ip_stocks = ProxyStock.objects.filter(cidr_id__in=cidr_ids, acl_id=acl_id, cart_step=step,
                                              exclude_label=False).all()
        total = ip_stocks.aggregate(total_stock=Sum('ip_stock'))['total_stock']
        # 如果没有ip_stocks，aggregate方法可能返回None
        if total is None:
            total = 0
        self.stock = total
        # logging.info(
        #     '更新产品:{} ProductStock:{} 库存:{} acl:{}'.format(self.product.product_name, self.id, self.stock,
        #                                                         self.acl.name))
        return self.stock


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

    def is_expired(self):
        """
        判断是否过期
        :return:
        """
        if self.expired_at:
            return self.expired_at < datetime.datetime.now()
        else:
            return False


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


@receiver(m2m_changed, sender=Cidr.exclude_acl.through)
def _mymodel_m2m_changed_cidr(sender, instance, action, reverse, model, pk_set, **kwargs):
    logging.info('cidr exclude_acl changed,action:{}'.format(action))
    if action in ["post_add", "post_remove", "post_clear"]:
        cidr = instance
        exclude_acls = instance.exclude_acl.all().values_list('id', flat=True)
        ip_stocks = ProxyStock.objects.filter(cidr=cidr).all()
        for stock in ip_stocks:
            stock.exclude_label = stock.acl_id in exclude_acls
            stock.save()


@receiver(pre_save, sender=ProxyStock)
def proxy_stock_updated_pre(sender, instance, **kwargs):
    if instance.available_subnets:
        available_subnets = instance.available_subnets.split(',')
        # 去除空字符串
        available_subnets = [x for x in available_subnets if x]
        instance.available_subnets = ','.join(available_subnets)
        instance.ip_stock = sum([ipaddress.ip_network(x).num_addresses for x in available_subnets])
    else:
        instance.ip_stock = 0
    print(instance.ip_stock)


@receiver(post_save, sender=ProxyStock)
def proxy_stock_updated_post(sender, instance, **kwargs):
    cidr_id = instance.cidr.id
    acl_id = instance.acl_id
    cart_step = instance.cart_step
    for product_stock in ProductStock.objects.filter(acl_id=acl_id, cart_step=cart_step).all():
        cidr_ids = [x.id for x in product_stock.server_group.get_cidrs()]
        if cidr_id in cidr_ids:
            print('更新产品库存{}'.format(product_stock.id))
            product_stock.save()


@receiver(pre_save, sender=ProductStock)
def _mymodel_pre_save(sender, instance, **kwargs):
    instance.count_stock()


@receiver(post_save, sender=ProductStock)
def update_product_stock_cache(sender, instance, **kwargs):
    """
    更新产品库存缓存
    :param sender:
    :param instance:
    :param kwargs:
    :return:
    """
    redis_client = cache.client.get_client()
    redis_client.hset('product_stocks', instance.id, instance.stock)


@receiver(post_delete, sender=Proxy)
def _mymodel_delete(sender, instance, **kwargs):
    from django.core.cache import cache
    delete_cache_key = 'delete_proxy_task:{}_{}'.format(instance.server_ip, instance.username)
    if not cache.get(delete_cache_key):
        cache.set(delete_cache_key, 1, timeout=60 * 3)
        # 通知删除代理
        from apps.proxy_server.tasks import delete_proxy_task
        delete_proxy_task.delay(instance.server_ip, instance.username)
    redis_key = 'stock_return_task:{}_{}'.format(instance.ip_stock_ids, instance.subnet)
    if not cache.get(redis_key):
        redis_key = 'stock_return_task:{}_{}'.format(instance.ip_stock_ids, instance.subnet)
        cache.set(redis_key, 1, timeout=60 * 5)
        # 通知回收库存
        from apps.proxy_server.tasks import stock_return_task
        stock_return_task.delay(instance.ip_stock_ids, instance.subnet)
    # # 归还子网,归还库存
    # if stock:
    #     if Proxy.objects.filter(subnet=instance.subnet, ip_stock_id=stock.id).count() == 0:
    #         with cache.lock(redis_key):
    #             logging.info('归还子网{},归还库存{}'.format(instance.subnet, instance.ip_stock_id))
    #             stock.return_subnet(instance.subnet)
    #             stock.return_stock()


@receiver(m2m_changed, sender=ServerGroup.servers.through)
def _mymodel_m2m_changed_server_group(sender, instance, action, reverse, model, pk_set, **kwargs):
    """
    服务器组变更修改varaints的cidr
    """
    if action == 'post_add' or action == 'post_remove':
        for v in instance.variants.all():
            v.cidrs.clear()
            v.cidrs.add(*instance.get_cidrs())


@receiver(m2m_changed, sender=Server.cidrs.through)
def _mymodel_m2m_changed_server(sender, instance, action, reverse, model, pk_set, **kwargs):
    """
    服务器变更修改varaints的cidr
    """
    if action == 'post_add' or action == 'post_remove':
        server_groups = instance.server_groups.all()
        for server_group in server_groups:
            for v in server_group.variants.all():
                v.cidrs.clear()
                v.cidrs.add(*server_group.get_cidrs())
