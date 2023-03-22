from apps.core.models import BaseModel
from django.db import models

# Create your models here.


class AclList(BaseModel):
    name = models.CharField(max_length=255, blank=True, null=True, verbose_name='ACL名')
    description = models.CharField(max_length=255, blank=True, null=True, verbose_name='描述')
    acl_value = models.TextField(blank=True, null=True, verbose_name='ACL值')

    class Meta:
        db_table = 'acl_list'
        verbose_name = 'ACL列表'
        verbose_name_plural = 'ACL列表'


class ProxyServer(BaseModel):
    name = models.CharField(max_length=255, blank=True, null=True, verbose_name='服务器名')
    description = models.CharField(max_length=255, blank=True, null=True, verbose_name='描述')
    ip = models.CharField(max_length=255, blank=True, null=True, verbose_name='IP')
    cidr_prefix = models.IntegerField(blank=True, null=True, verbose_name='CIDR前缀')

    class Meta:
        db_table = 'proxy_server'
        verbose_name = '代理服务器'
        verbose_name_plural = '代理服务器'


class ProxyList(models.Model):
    ip = models.CharField(max_length=255, blank=True, null=True, verbose_name='IP')
    username = models.CharField(max_length=255, blank=True, null=True, verbose_name='用户名')
    password = models.CharField(max_length=255, blank=True, null=True, verbose_name='密码')
    port = models.IntegerField(blank=True, null=True, verbose_name='端口')
    proxy_type = models.CharField(max_length=255, blank=True, null=True, verbose_name='类型')
    server_id = models.IntegerField(blank=True, null=True, verbose_name='服务器ID')
    acl_ids = models.CharField(max_length=255, blank=True, null=True, verbose_name='ACL IDs')

    class Meta:
        db_table = 'proxy_list'
        verbose_name = '代理列表'
        verbose_name_plural = '代理列表'
