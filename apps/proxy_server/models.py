from apps.core.models import BaseModel
from django.db import models


# Create your models here.
class AclGroup(BaseModel):
    name = models.CharField(max_length=255, blank=True, null=True, verbose_name='ACL组名')
    description = models.CharField(max_length=255, blank=True, null=True, verbose_name='描述')
    acls = models.ManyToManyField('Acls', verbose_name='ACL', through='AclGroupThrough')
    acl_value = models.CharField(max_length=1024, null=True, verbose_name='ACL值')

    class Meta:
        db_table = 'acl_group'
        verbose_name = 'ACL组'
        verbose_name_plural = 'ACL组'


class Acls(BaseModel):
    name = models.CharField(max_length=255, blank=True, null=True, verbose_name='ACL名')
    description = models.CharField(max_length=255, blank=True, null=True, verbose_name='描述')
    acl_value = models.TextField(blank=True, null=True, verbose_name='ACL值')

    class Meta:
        db_table = 'acls'
        verbose_name = '访问控制列表'
        verbose_name_plural = '访问控制列表'

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
    servers = models.ManyToManyField('Server', verbose_name='服务器',through='ServerGroupThrough')

    class Meta:
        db_table = 'server_group'
        verbose_name = '服务器组'
        verbose_name_plural = '服务器组'
class ServerGroupThrough(BaseModel):
    server_group = models.ForeignKey('ServerGroup', on_delete=models.CASCADE, blank=True, null=True, verbose_name='服务器组')
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
    class Meta:
        db_table = 'server'
        verbose_name = '代理服务器'
        verbose_name_plural = '代理服务器'
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
class Cidr(BaseModel):
    cidr = models.CharField(max_length=255, blank=True, null=True, verbose_name='CIDR')
    ip_count = models.IntegerField(blank=True, null=True, verbose_name='IP数量')
    class Meta:
        db_table = 'cidr'
        verbose_name = 'CIDR'
        verbose_name_plural = 'CIDR'
class ServerCidrThrough(BaseModel):
    server = models.ForeignKey('Server', on_delete=models.CASCADE, blank=True, null=True, verbose_name='服务器')
    cidr = models.ForeignKey('Cidr', on_delete=models.CASCADE, blank=True, null=True, verbose_name='CIDR')
    class Meta:
        db_table = 'server_cidr_through'
        verbose_name = '服务器与CIDR关系'
        verbose_name_plural = '服务器与CIDR关系'
# 库存表
class ProxyStock(BaseModel):
    cidr = models.ForeignKey('Cidr', on_delete=models.CASCADE, blank=True, null=True, verbose_name='CIDR')
    acl_group = models.ForeignKey('AclGroup', on_delete=models.CASCADE, blank=True, null=True, verbose_name='ACL组')
    ip_stock = models.IntegerField(blank=True, null=True, verbose_name='IP数量')
    variant_id = models.IntegerField(blank=True, null=True, verbose_name='变体ID')
    cart_step = models.IntegerField(blank=True, null=True, verbose_name='购物车步长')
    cart_stock = models.IntegerField(blank=True, null=True, verbose_name='购物车库存')
    class Meta:
        db_table = 'ip_stock'
        verbose_name = 'IP库存'
        verbose_name_plural = 'IP库存'


class Proxy(BaseModel):
    ip = models.CharField(max_length=255, blank=True, null=True, verbose_name='IP')
    username = models.CharField(max_length=255, blank=True, null=True, verbose_name='用户名')
    password = models.CharField(max_length=255, blank=True, null=True, verbose_name='密码')
    port = models.IntegerField(blank=True, null=True, verbose_name='端口')
    proxy_type = models.CharField(max_length=255, blank=True, null=True, verbose_name='类型')
    server_id = models.IntegerField(blank=True, null=True, verbose_name='服务器ID')
    acl_groups = models.ManyToManyField('AclGroup', verbose_name='ACL组')
    order = models.ForeignKey('orders.Orders', on_delete=models.CASCADE, blank=True, null=True, verbose_name='订单')
    expired_at = models.DateTimeField(blank=True, null=True, verbose_name='过期时间')
    user= models.ForeignKey('users.User', on_delete=models.CASCADE, blank=True, null=True, verbose_name='用户')

    class Meta:
        db_table = 'proxy'
        verbose_name = '代理列表'
        verbose_name_plural = '代理列表'
