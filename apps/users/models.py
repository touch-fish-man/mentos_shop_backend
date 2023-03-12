from uuid import uuid4

from django.db import models,transaction

# Create your models here.
from django.contrib.auth.models import AbstractUser


class UserProfile(AbstractUser):
    """用户信息表"""
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=100, unique=True, verbose_name='用户名')
    email = models.EmailField(max_length=100, unique=True)
    password = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    discord_id = models.CharField(max_length=100, unique=True)
    is_superuser = models.BooleanField(default=False)
    level = models.IntegerField(default=0)
    points = models.IntegerField(default=0)
    uid=models.UUIDField("uid", null=True, unique=True)

    last_login = models.DateTimeField(auto_now=True)
    invite_code = models.CharField(max_length=100, unique=True)
    invite_code_used = models.CharField(max_length=100)
    invite_user_id = models.IntegerField(default=0)

    class Meta:
        db_table = 'users'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username
    @classmethod
    @transaction.atomic
    def add_user(cls, user_data):
        user_data["uid"] = str(uuid4())
        user = cls.objects.create_user(**user_data)
        user.save()
        return user

    def update_user(self, username, email, password, discord_id, invite_code, invite_code_used, invite_user_id):
        self.username = username
        self.email = email
        self.password = password
        self.discord_id = discord_id
        self.invite_code = invite_code
        self.invite_code_used = invite_code_used
        self.invite_user_id = invite_user_id
        self.save()
        return self

    def delete_user(self):
        self.delete()
        return self

    def get_user_by_id(self, user_id):
        return self.objects.get(user_id=user_id)

class InviteCode(models.Model):
    """邀请码表"""
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=100, unique=True)
    user_id = models.IntegerField(default=0)
    is_used = models.BooleanField(default=False)
    used_time = models.DateTimeField(auto_now=True)
    create_time = models.DateTimeField(auto_now=True)


class UserOrder(models.Model):
    DEFAULT_ORDER_TIME_OUT = "10m"
    STATUS_CREATED = 0
    STATUS_PAID = 1
    STATUS_FINISHED = 2
    STATUS_CHOICES = (
        (STATUS_CREATED, "created"),
        (STATUS_PAID, "paid"),
        (STATUS_FINISHED, "finished"),
    )

    user_id = models.ForeignKey(UserProfile, on_delete=models.CASCADE, verbose_name="用户")
    status = models.SmallIntegerField(
        verbose_name="订单状态", db_index=True, choices=STATUS_CHOICES
    )
    out_trade_no = models.CharField(
        verbose_name="订单号", max_length=64, unique=True, db_index=True
    )
    qrcode_url = models.CharField(verbose_name="支付连接", max_length=512, null=True)
    amount = models.DecimalField(
        verbose_name="金额", decimal_places=2, max_digits=10, default=0
    )
    created_at = models.DateTimeField(
        verbose_name="时间", auto_now_add=True, db_index=True
    )
    expired_at = models.DateTimeField(verbose_name="过期时间", db_index=True)

    def __str__(self):
        return f"<{self.id, self.user_id}>:{self.amount}"

    class Meta:
        verbose_name = "用户订单"
        verbose_name_plural = "用户订单"
        index_together = ["user_id", "status"]
