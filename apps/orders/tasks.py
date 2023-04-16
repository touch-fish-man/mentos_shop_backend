from __future__ import absolute_import
import datetime
import pytz
from celery.schedules import crontab
from apps import celery_app
from apps.orders.models import Orders
from apps.proxy_server.models import Proxy
from apps.users.models import User
from apps.users.services import send_via_sendgrid,send_email_via_mailgun
from django.conf import settings
from django.core.mail import send_mail

@celery_app.task(name='precheck_order_expired')
def precheck_order_expired(ceheck_days=3,send_email=True):
    """
    定时检查db中订单状态，如果订单即将过期，发送续费邮件，每天检查一次
    """
    utc_now = datetime.datetime.now(tz=pytz.utc)
    utc_today = utc_now.date()
    orders = Orders.objects.filter(order_status=1).values('expired_at','order_id','uid')
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


@celery_app.task(name='check_order_expired')
def check_order_expired():
    """
    定时检查db中订单状态，如果订单已过期，删除代理，每天检查一次，添加当天过期删除任务
    """
    orders = Orders.objects.values('order_status','id')
    for order in orders:
        if order['order_status']==3:
            delete_proxy_expired(order['id'])

def delete_proxy_expired(order_id):
    """
    删除过期代理
    """
    Proxy.objects.filter(order_id=order_id).delete()

celery_app.conf.beat_schedule = {
    'precheck_order_expired': {
        'task': 'precheck_order_expired',
        'schedule': crontab(hour=6, minute=0),
    },
    'check_order_expired':{
        'task': 'check_order_expired',
        'schedule': crontab(hour=1, minute=0),
    }
}