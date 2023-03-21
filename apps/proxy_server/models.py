from django.db import models

# Create your models here.


class AclList(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, blank=True, null=True,verbose_name='ACL名')
    description = models.CharField(max_length=255, blank=True, null=True,verbose_name='描述')
    acl_value = models.TextField(blank=True, null=True,verbose_name='ACL值')
    created_at = models.DateTimeField(blank=True, null=True,verbose_name='创建时间')
    updated_at = models.DateTimeField(blank=True, null=True,verbose_name='更新时间')

    class Meta:
        managed = False
        db_table = 'acl_list'


class ProxyServer(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, blank=True, null=True,verbose_name='服务器名')
    description = models.CharField(max_length=255, blank=True, null=True,verbose_name='描述')
    ip = models.CharField(max_length=255, blank=True, null=True,verbose_name='IP')
    cidr_prefix = models.IntegerField(blank=True, null=True,verbose_name='CIDR前缀')
    created_at = models.DateTimeField(blank=True, null=True,verbose_name='创建时间')
    updated_at = models.DateTimeField(blank=True, null=True,verbose_name='更新时间')

    class Meta:
        managed = False
        db_table = 'proxy_server'


class ProxyServerGroup(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, blank=True, null=True,verbose_name='组名')
    description = models.CharField(max_length=255, blank=True, null=True,verbose_name='描述')
    proxy_server_ids = models.CharField(max_length=255, blank=True, null=True,verbose_name='服务器ID')
    created_at = models.DateTimeField(blank=True, null=True,verbose_name='创建时间')
    updated_at = models.DateTimeField(blank=True, null=True,verbose_name='更新时间')

    class Meta:
        managed = False
        db_table = 'proxy_server_group'


class Proxy(models.Model):
    id = models.AutoField(primary_key=True)
    ip = models.CharField(max_length=255, blank=True, null=True,verbose_name='IP')
    username = models.CharField(max_length=255, blank=True, null=True,verbose_name='用户名')
    password = models.CharField(max_length=255, blank=True, null=True,verbose_name='密码')
    port = models.IntegerField(blank=True, null=True,verbose_name='端口')
    proxy_type = models.CharField(max_length=255, blank=True, null=True,verbose_name='类型')
    server_id = models.IntegerField(blank=True, null=True,verbose_name='服务器ID')
    acl_ids = models.CharField(max_length=255, blank=True, null=True,verbose_name='ACL ID')
    created_at = models.DateTimeField(blank=True, null=True,verbose_name='创建时间')
    updated_at = models.DateTimeField(blank=True, null=True,verbose_name='更新时间')

    class Meta:
        managed = False
        db_table = 'proxy'
