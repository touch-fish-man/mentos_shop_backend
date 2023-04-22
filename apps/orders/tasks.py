from __future__ import absolute_import
import datetime
import pytz
from celery.schedules import crontab
from apps.orders.models import Orders
from apps.proxy_server.models import Proxy
from apps.users.models import User
from apps.users.services import send_via_sendgrid,send_email_via_mailgun
from django.conf import settings
from django.core.mail import send_mail
from apps.utils.kaxy_handler import KaxyClient
from celery import shared_task

@shared_task(name='precheck_order_expired')
def precheck_order_expired(ceheck_days=3,send_email=True):
    """
    定时检查db中订单状态，如果订单即将过期，发送续费邮件，每天检查一次
    """
    utc_now = datetime.datetime.now(tz=pytz.utc)
    utc_today = utc_now.date()
    orders = Orders.objects.filter(order_status=4).values('expired_at','order_id','uid')
    for order in orders:
        precheck_day = (order['expired_at']-datetime.timedelta(days=ceheck_days)).date()
        if utc_today == precheck_day:
            email = User.objects.get(id=order['uid']).email
            email_template=settings.EMAIL_TEMPLATES.get('notification')
            subject = email_template.get('subject')
            html_message = email_template.get('html').replace('{{order_id}}', str(order['order_id']))
            from_email = email_template.get('from_email')
            if settings.EMAIL_METHOD == 'sendgrid':
                send_via_sendgrid(email, subject, from_email, html_message)
            elif settings.EMAIL_METHOD == 'mailgun':
                send_email_via_mailgun(email, subject, from_email, html_message)
            else:
                send_mail(subject, "", from_email, [email], html_message=html_message)


@shared_task(name='check_order_expired')
def check_order_expired():
    """
    定时检查db中订单状态，如果订单已过期，删除代理，每天检查一次，添加当天过期删除任务
    """
    utc_now = datetime.datetime.now(tz=pytz.utc)
    utc_today = utc_now.date()
    orders = Orders.objects.all().values('id','expired_at')
    for order in orders:
        expired_day = order['expired_at'].date()
        if utc_today == expired_day and utc_now<order['expired_at']:
            change_order.apply_async(args=[order['id']], eta=order['expired_at'])
        elif utc_today == expired_day and utc_now>order['expired_at']:
            change_order.apply_async(args=[order['id']], eta=utc_now+datetime.timedelta(minutes=5))

@shared_task(name='change_order')
def change_order(order_id):
    Orders.objects.filter(id=order_id).update(order_status=3)
    proxys = Proxy.objects.filter(order_id=order_id)
    server_ip = proxys.first().server_ip
    client = KaxyClient(server_ip)
    for proxy in proxys:
        if proxy.server_ip != server_ip:
            server_ip = proxy.server_ip
            client.del_user(proxy.username)
            client = KaxyClient(server_ip)
    proxys.delete()

@shared_task(name='delete_proxy_expired')
def delete_proxy_expired():
    """
    删除过期代理
    """
    del_user_dict = {}
    all_proxy=Proxy.objects.filter().all()
    for proxy in all_proxy:
        if proxy.expired_at < datetime.datetime.now(tz=pytz.utc):
            if proxy.server_ip not in del_user_dict:
                del_user_dict[proxy.server_ip] = set()
            del_user_dict[proxy.server_ip].add(proxy.username)
            proxy.delete()
    for s_ip,users in del_user_dict.items():
        for user in users:
            client=KaxyClient(s_ip)
            client.del_user(user)
