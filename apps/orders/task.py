from celery import shared_task
from apps.orders.models import Orders
from apps.proxy_server.models import Proxy
from apps.users.services import send_via_sendgrid,send_email_via_mailgun
from apps.users.models import User
from djcelery.models import CrontabSchedule,PeriodicTask
from django.conf import settings
from django.core.mail import send_mail
import datetime
import json
@shared_task
def notification(email,order_id):
    email_template=settings.EMAIL_TEMPLATES.get('notification')
    subject = email_template.get('subject')
    html_message = email_template.get('html').replace('{{order_id}}', order_id)
    from_email = email_template.get('from_email')
    if settings.EMAIL_METHOD == 'sendgrid':
        send_via_sendgrid(email, subject, from_email, html_message)
    elif settings.EMAIL_METHOD == 'mailgun':
        send_email_via_mailgun(email, subject, from_email, html_message)
    else:
        send_mail(subject, "", from_email, [email], html_message=html_message)


@shared_task
def email_notification(order_id):
    expired_at = Orders.objects.filter(id=order_id).values('expired_at')
    start_time = datetime.datetime.strptime(expired_at,"%Y-%m-%d %H:%M:%S")
    uid = Orders.objects.filter(id=order_id).values('uid')
    email= User.objects.filter(uid=uid).values('email')
    cron_objc=CrontabSchedule(
        minute=str(start_time.minute),
        hour=str(start_time.hour),
        day_of_month=str(start_time.day),
        month_of_year=str(start_time.month),
        year_of_month=str(start_time.year)
    )
    cron_objc.save()
    task_kwargs ={'order_id':order_id}
    task,create = PeriodicTask.objects.create(
        kwargs=json.dumps(task_kwargs),
        name='notification',
        task='apps.orders.task.notification',
        cron_objc=cron_objc.id
    )
    task.save()
    if create:
        print("成功")
    else:
        print("失败")

@shared_task
def del_proxy(order_id):
    proxy = Proxy.objects.filter(order_id=order_id)
    proxy.delete()


@shared_task
def del_order_proxy(order_id):
    expired_at = Orders.objects.filter(id=order_id).values('expired_at')
    start_time = datetime.datetime.strptime(expired_at,"%Y-%m-%d %H:%M:%S")
    cron_objc=CrontabSchedule(
        minute=str(start_time.minute),
        hour=str(start_time.hour),
        day_of_month=str(start_time.day),
        month_of_year=str(start_time.month),
        year_of_month=str(start_time.year)
    )
    cron_objc.save()
    task_kwargs ={'order_id':order_id}
    task,create = PeriodicTask.objects.create(
        kwargs=json.dumps(task_kwargs),
        name='del_proxy',
        task='apps.orders.task.del_proxy',
        cron_objc=cron_objc.id
    )
    task.save()
    if create:
        print("成功")
    else:
        print("失败")