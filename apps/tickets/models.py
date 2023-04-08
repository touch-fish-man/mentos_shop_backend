from apps.core.models import BaseModel
from django.db import models


class Tickets(models.Model):
    username = models.CharField(max_length=100, verbose_name='用户名')
    email = models.EmailField(max_length=100, verbose_name='邮箱')
    phone = models.CharField(max_length=11, verbose_name='手机号')
    message = models.TextField(verbose_name='客户信息')

    class Meta:
        db_table = 'tickets'
        verbose_name = '工单'
        verbose_name_plural = verbose_name


class Question(models.Model):
    '''
    FAQ
    '''
    question = models.CharField(max_length=200)
    answer = models.TextField()
