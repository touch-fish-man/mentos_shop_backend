from uuid import uuid4

from django.db import models, transaction

# Create your models here.
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """用户信息表"""
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=100, unique=True, verbose_name='用户名')
    email = models.EmailField(max_length=100, unique=True, verbose_name='邮箱')
    password = models.CharField(max_length=100, verbose_name='密码')
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    discord_id = models.CharField(max_length=100, unique=True, null=True, verbose_name='discord_id')
    is_superuser = models.BooleanField(default=False, verbose_name='是否超级管理员')
    level = models.IntegerField(default=0, verbose_name='等级')
    points = models.IntegerField(default=0, verbose_name='积分')
    uid = models.UUIDField("uid", null=True, unique=True, default=uuid4, editable=False, help_text="用户唯一标识")
    last_login = models.DateTimeField(auto_now=True)
    invite_code = models.CharField(max_length=100, unique=True)
    invite_user_id = models.IntegerField(default=0)
    is_admin = models.BooleanField(default=False, verbose_name='是否管理员')

    class Meta:
        db_table = 'users'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username

    @classmethod
    @transaction.atomic
    def add_user(cls, user_data):
        user = cls.objects.create_user(**user_data)
        user.save()
        return user

    def bind_discord(self, discord_id):
        self.discord_id = discord_id
        self.save()
        return self

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
    id = models.AutoField(primary_key=True, verbose_name='id')
    code = models.CharField(max_length=100, unique=True, verbose_name='邀请码')
    user_id = models.IntegerField(default=0, verbose_name='用户id')
    invite_count = models.IntegerField(default=0, verbose_name='邀请人数')
    invite_reward = models.IntegerField(default=0, verbose_name='邀请奖励')
    create_time = models.DateTimeField(auto_now=True, verbose_name='创建时间')

    class Meta:
        db_table = 'invite_code'
        verbose_name = '邀请码'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.code

    @classmethod
    @transaction.atomic
    def gen_invite_code(cls, user_id):
        if cls.objects.filter(user_id=user_id).exists():
            return cls.objects.get(user_id=user_id)
        invite_code = cls.objects.create(user_id=user_id)
        invite_code.save()
        return invite_code

    @classmethod
    def get_invite_code_by_user_id(cls, user_id):
        return cls.objects.get(user_id=user_id)

    @classmethod
    def add_invite_count_by_code(cls, code):
        invite_code = cls.objects.get(code=code)
        invite_code.invite_count += 1
        invite_code.save()
        return invite_code

    @classmethod
    def get_inviter_by_code(cls, code):
        return cls.objects.get(code=code).user_id


class InviteLog(models.Model):
    """邀请记录表"""
    id = models.AutoField(primary_key=True)
    user_id = models.IntegerField(verbose_name="用户id")
    invite_user_id = models.IntegerField(verbose_name="邀请人id")
    invite_code = models.CharField(max_length=100, verbose_name="邀请码")
    used_time = models.DateTimeField(auto_now=True, verbose_name="使用时间")
    create_time = models.DateTimeField(auto_now=True, verbose_name="创建时间")

    class Meta:
        db_table = 'invite_log'
        verbose_name = '邀请记录'
        verbose_name_plural = verbose_name
class RebateRecord(models.Model):
    """返利记录"""

    user_id = models.PositiveIntegerField(verbose_name="返利人ID", default=1)
    consumer_id = models.PositiveIntegerField(
        verbose_name="消费者ID", null=True, blank=True
    )
    money = models.DecimalField(
        verbose_name="金额",
        decimal_places=2,
        null=True,
        default=0,
        max_digits=10,
        blank=True,
    )
    create_time = models.DateTimeField(editable=False, auto_now_add=True)

    class Meta:
        db_table = "rebate_record"
        verbose_name = "返利记录"
        verbose_name_plural = verbose_name
        ordering = ("-create_time",)

    @classmethod
    def list_by_user_id_with_consumer_username(cls, user_id, num=10):
        logs = cls.objects.filter(user_id=user_id)[:num]
        user_ids = [log.consumer_id for log in logs]
        username_map = {u.id: u.username for u in User.objects.filter(id__in=user_ids)}
        for log in logs:
            setattr(log, "consumer_username", username_map.get(log.consumer_id, ""))
        return logs

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

    user_id = models.PositiveIntegerField(verbose_name="用户ID", db_index=True)
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
        db_table = "user_order"
        verbose_name = "用户订单"
        verbose_name_plural = "用户订单"
        index_together = ["user_id", "status"]

class Code(models.Model):
    """邮箱验证码表"""
    email = models.EmailField() # 用户邮箱
    code = models.CharField(max_length=6) # 验证码
    create_time = models.IntegerField() # 创建时间

    class Meta:
        db_table = 'code'
        verbose_name = '邮箱验证码'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.email + ':' + self.code
