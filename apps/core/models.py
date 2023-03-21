from django.db import models

# Create your models here.
class BaseModel(models.Model):
    id = models.AutoField(primary_key=True,verbose_name='id')
    created_at = models.DateTimeField(blank=True, null=True,verbose_name='创建时间',auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True,verbose_name='更新时间',auto_now=True)

    class Meta:
        abstract = True