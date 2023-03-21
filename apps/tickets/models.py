from django.db import models

# Create your models here.
class WorkOrder(models.Model):
    username = models.CharField(max_length=100, verbose_name='用户名')
    email = models.EmailField(max_length=100, verbose_name='邮箱')
    phone = models.CharField(max_length=11, verbose_name='手机号')
    message = models.TextField(verbose_name='客户信息')