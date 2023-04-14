from __future__ import absolute_import
from celery import shared_task
from apps.orders.models import Orders
from apps.proxy_server.models import Proxy
from apps.users.models import User


def precheck_order_expired(ceheck_days=3,send_email=True):
    """
    定时检查db中订单状态，如果订单即将过期，发送续费邮件，每天检查一次
    """
    pass


def check_order_expired():
    """
    定时检查db中订单状态，如果订单已过期，删除代理，每天检查一次，添加当天过期删除任务
    """
    pass

def delete_proxy_expired():
    """
    删除过期代理
    """
    pass