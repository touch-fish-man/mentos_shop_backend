import ipaddress
import json
import math

from apps.core.models import BaseModel
from django.db import models


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


class Cidr(BaseModel):
    cidr = models.CharField(max_length=255, blank=True, null=True, verbose_name='CIDR')
    ip_count = models.IntegerField(blank=True, null=True, verbose_name='IP数量')

    class Meta:
        db_table = 'cidr'
        verbose_name = 'CIDR'
        verbose_name_plural = 'CIDR'


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


# 库存表
class ProxyStock(BaseModel):
    cidr = models.ForeignKey('Cidr', on_delete=models.CASCADE, blank=True, null=True, verbose_name='CIDR')
    acl_group = models.ForeignKey('AclGroup', on_delete=models.CASCADE, blank=True, null=True, verbose_name='ACL组')
    ip_stock = models.IntegerField(blank=True, null=True, verbose_name='IP数量')
    variant_id = models.IntegerField(blank=True, null=True, verbose_name='变体ID')
    cart_step = models.IntegerField(blank=True, null=True, verbose_name='购物车步长')
    cart_stock = models.IntegerField(blank=True, null=True, verbose_name='购物车库存')
    current_subnet = models.CharField(max_length=255, blank=True, null=True, verbose_name='当前子网')
    subnets = models.TextField(blank=True, null=True, verbose_name='子网') # 用于存储所有子网

    class Meta:
        db_table = 'ip_stock'
        verbose_name = 'IP库存'
        verbose_name_plural = 'IP库存'

    def gen_subnets(self):
        """
        生成子网
        :return:
        """
        # 计算
        subnets = self.get_all_subnet(self.cidr.cidr, new_prefix=32 - int(math.log(self.cart_step, 2)))
        self.subnets = ",".join(subnets)
        self.save()
        return subnets
    def get_next_subnet(self):
        """
        获取下一个子网
        :return:
        """
        subnets = self.subnets.split(',')
        if self.current_subnet:
            index = subnets.index(self.current_subnet)
            if index + 1 < len(subnets):
                return subnets[index + 1]
            else:
                return None
        else:
            return subnets[0]

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


class Proxy(BaseModel):
    ip = models.CharField(max_length=255, blank=True, null=True, verbose_name='IP')
    username = models.CharField(max_length=255, blank=True, null=True, verbose_name='用户名')
    password = models.CharField(max_length=255, blank=True, null=True, verbose_name='密码')
    port = models.IntegerField(blank=True, null=True, verbose_name='端口')
    proxy_type = models.CharField(max_length=255, blank=True, null=True, verbose_name='类型')
    server_ip = models.CharField(max_length=255, blank=True, null=True, verbose_name='服务器IP')
    order = models.ForeignKey('orders.Orders', on_delete=models.CASCADE, blank=True, null=True, verbose_name='订单')
    expired_at = models.DateTimeField(blank=True, null=True, verbose_name='过期时间')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, blank=True, null=True, verbose_name='用户')

    class Meta:
        db_table = 'proxy'
        verbose_name = '代理列表'
        verbose_name_plural = '代理列表'
    def delete(self, using=None, keep_parents=False):
        """
        删除代理
        """
        # 如果数据库中username剩下最后一个，删除用户
        if Proxy.objects.filter(username=self.username).count() == 1:
            # 从kaxy中删除用户
            # todo
            pass
        # 删除代理
        super(Proxy, self).delete(using, keep_parents)
