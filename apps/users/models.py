from uuid import uuid4

from django.db import models, transaction

# Create your models here.
from django.contrib.auth.models import AbstractUser
from apps.core.models import BaseModel


def gen_uid():
    # 生成8位uuid
    return str(uuid4()).replace('-', '')[:8]


def gen_invite_code():
    # 生成8位uuid
    return str(uuid4()).replace('-', '')[:8]


class User(AbstractUser, BaseModel):
    """用户信息表"""
    LEVEL_CHOICES = (
        (1, 'VIP1用户'),
        (2, 'VIP2用户'),
        (3, 'VIP3用户'),
        (4, 'VIP4用户'),
        (5, 'VIP5用户')
    )
    uid = models.CharField(max_length=100, unique=True, null=True, verbose_name='用户uid', default=gen_uid)
    username = models.CharField(max_length=100, unique=True, verbose_name='用户名')
    email = models.EmailField(max_length=100, unique=True, verbose_name='邮箱')
    password = models.CharField(max_length=100, verbose_name='密码')
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    discord_id = models.CharField(max_length=100, unique=True, null=True, verbose_name='discord_id')
    discord_name = models.CharField(max_length=100, null=True, verbose_name='discord_name')
    is_superuser = models.BooleanField(default=False, verbose_name='是否超级管理员')
    level = models.IntegerField(default=1, verbose_name='等级', choices=LEVEL_CHOICES)
    level_points = models.IntegerField(default=100, verbose_name='等级积分')
    reward_points = models.IntegerField(default=0, verbose_name='邀请奖励')
    invite_code = models.CharField(max_length=100, unique=True, null=True, verbose_name='邀请码',
                                   default=gen_invite_code)
    invite_count = models.IntegerField(default=0, verbose_name='邀请人数')
    # invite_reward = models.IntegerField(default=0, verbose_name='邀请奖励')

    def __str__(self):
        return self.username

    class Meta:
        db_table = 'user'
        verbose_name = '用户'
        verbose_name_plural = verbose_name


# class InviteCode(BaseModel):
#     """邀请码表"""
#     id = models.AutoField(primary_key=True, verbose_name='id')
#     invite_code = models.CharField(max_length=100, unique=True, verbose_name='邀请码')
#     uid = models.IntegerField(default=0, verbose_name='用户uid')
#     invite_count = models.IntegerField(default=0, verbose_name='邀请人数')
#     invite_reward = models.IntegerField(default=0, verbose_name='邀请奖励')
#
#     class Meta:
#         db_table = 'invite_code'
#         verbose_name = '邀请码'
#         verbose_name_plural = verbose_name
#
#     def __str__(self):
#         return self.invite_code


class InviteLog(BaseModel):
    """邀请记录表"""
    id = models.AutoField(primary_key=True)
    uid = models.IntegerField(verbose_name="用户id")
    inviter_uid = models.IntegerField(verbose_name="邀请人id")
    invite_code = models.CharField(max_length=100, verbose_name="邀请码")

    class Meta:
        db_table = 'invite_log'
        verbose_name = '邀请记录'
        verbose_name_plural = verbose_name


class RebateRecord(BaseModel):
    """邀请人返利记录"""

    uid = models.PositiveIntegerField(verbose_name="返利人ID", default=1)
    consumer_uid = models.PositiveIntegerField(
        verbose_name="消费者ID", null=True, blank=True
    )
    money = models.PositiveIntegerField(verbose_name="返利金额", default=0)

    class Meta:
        db_table = "rebate_record"
        verbose_name = "返利记录"
        verbose_name_plural = verbose_name
        ordering = ("-created_at",)


class UserLevlRecord(BaseModel):
    """用户等级记录表"""
    uid = models.IntegerField(verbose_name="用户uid")
    level = models.IntegerField(verbose_name="等级")
    level_points = models.IntegerField(verbose_name="等级积分")

    class Meta:
        db_table = 'user_level_record'
        verbose_name = '用户等级记录'
        verbose_name_plural = verbose_name


class UserOrder(BaseModel):
    STATUS_CREATED = 0
    STATUS_PAID = 1
    STATUS_FINISHED = 2
    STATUS_CHOICES = (
        (STATUS_CREATED, "created"),
        (STATUS_PAID, "paid"),
        (STATUS_FINISHED, "finished"),
    )

    uid = models.PositiveIntegerField(verbose_name="用户ID", db_index=True)
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
    expired_at = models.DateTimeField(verbose_name="过期时间", db_index=True)

    def __str__(self):
        return f"<{self.id, self.uid}>:{self.amount}"

    class Meta:
        db_table = "user_order"
        verbose_name = "用户订单"
        verbose_name_plural = "用户订单"
        index_together = ["uid", "status"]


class Code(BaseModel):
    """邮箱验证码表"""
    email = models.EmailField()  # 用户邮箱
    code = models.CharField(max_length=6)  # 验证码
    verify_id = models.CharField(max_length=100)  # 验证id

    class Meta:
        db_table = 'code'
        verbose_name = '邮箱验证码'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.email + ':' + self.code
