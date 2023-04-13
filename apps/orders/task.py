from __future__ import absolute_import
from celery import shared_task
from apps.orders.models import Orders
from apps.proxy_server.models import Proxy
from apps.users.services import send_via_sendgrid,send_email_via_mailgun
from apps.users.models import User
from django.conf import settings
from django.core.mail import send_mail


def email_notification(order_id):
    print(str(order_id),type(order_id),type(str(order_id)))
    uid = Orders.objects.get(id=order_id).uid
    order_id = Orders.objects.get(id=order_id).order_id
    email= User.objects.get(uid=uid).email
    email_template=settings.EMAIL_TEMPLATES.get('notification')
    subject = email_template.get('subject')
    html_message = email_template.get('html').replace('{{order_id}}', str(order_id))
    from_email = email_template.get('from_email')
    if settings.EMAIL_METHOD == 'sendgrid':
        send_via_sendgrid(email, subject, from_email, html_message)
    elif settings.EMAIL_METHOD == 'mailgun':
        send_email_via_mailgun(email, subject, from_email, html_message)
    else:
        send_mail(subject, "", from_email, [email], html_message=html_message)
    

def del_proxy(order_id):
    proxy = Proxy.objects.filter(order_id=order_id)
    proxy.delete()
