from __future__ import absolute_import
import datetime
import json

import pytz
from celery.schedules import crontab
from apps.orders.models import Orders
from apps.orders.services import create_proxy
from apps.proxy_server.models import Proxy
from apps.users.models import User
from apps.users.services import send_via_sendgrid, send_email_via_mailgun
from django.conf import settings
from django.core.mail import send_mail
from apps.utils.kaxy_handler import KaxyClient
from celery import shared_task


@shared_task(name='precheck_order_expired')
def precheck_order_expired(ceheck_days=3, send_email=True):
    """
    定时检查db中订单状态，如果订单即将过期，发送续费邮件，每天检查一次
    """
    utc_now = datetime.datetime.now().astimezone(pytz.utc)
    utc_today = utc_now.date()
    expire_list = []
    orders = Orders.objects.filter(order_status=4).values('expired_at', 'order_id', 'uid', 'id')
    for order in orders:
        precheck_day = (order['expired_at'] - datetime.timedelta(days=ceheck_days)).date()
        if utc_today == precheck_day:
            expire_list.append(order['id'])
            email = User.objects.get(id=order['uid']).email
            email_template = settings.EMAIL_TEMPLATES.get('notification')
            subject = email_template.get('subject')
            html_message = email_template.get('html').replace('{{order_id}}', str(order['order_id']))
            from_email = email_template.get('from_email')
            if settings.EMAIL_METHOD == 'sendgrid':
                send_via_sendgrid(email, subject, from_email, html_message)
            elif settings.EMAIL_METHOD == 'mailgun':
                send_email_via_mailgun(email, subject, from_email, html_message)
            else:
                send_mail(subject, "", from_email, [email], html_message=html_message)
    data = {
        "expire_list": expire_list,
        "status": 1
    }
    return json.dumps(data)


def model_to_dict(instance):
    data = {}
    for field in instance._meta.fields:
        value = getattr(instance, field.name)
        if isinstance(value, datetime.datetime):
            data[field.name] = value.isoformat()
        else:
            data[field.name] = str(value)
    return data


@shared_task(name='check_order_expired')
def check_order_expired():
    """
    定时检查db中订单状态，如果订单过期，删除对应的proxy，每小时检查一次
    """
    utc_now = datetime.datetime.now().astimezone(pytz.utc)
    expired_orders = Orders.objects.filter(pay_status=1, order_status=4, expired_at__lte=utc_now).all()
    expired_order_ids = [order.id for order in expired_orders]
    orders_to_dict = {order.id: model_to_dict(order) for order in expired_orders}

    # 获取与这些订单关联的代理
    proxies_to_delete = Proxy.objects.filter(order_id__in=expired_order_ids)
    proxy_data = [(proxy.server_ip, proxy.username) for proxy in proxies_to_delete]

    # 删除代理并更新关联的订单
    for server_ip, username in proxy_data:
        try:
            client = KaxyClient(server_ip)
            client.del_user(username)
        except Exception as e:
            print(e)

    # 批量删除代理和更新订单状态
    proxies_to_delete.delete()
    Orders.objects.filter(id__in=expired_order_ids).update(order_status=3)

    data = {
        'orders': orders_to_dict,
        'status': 1
    }
    return json.dumps(data)


@shared_task(name='delete_proxy_expired')
def delete_proxy_expired():
    """
    删除过期代理,每天检查一次
    """
    delete_dict = {}
    all_proxy = Proxy.objects.all()
    for proxy in all_proxy:
        if proxy.expired_at < datetime.datetime.now().astimezone(pytz.utc):
            delete_dict[proxy.id] = model_to_dict(proxy)
            proxy.delete()
    data = {
        'proxies': delete_dict,
        'status': 1
    }
    return json.dumps(data)


@shared_task(name='delete_timeout_order')
def delete_timeout_order():
    """
    删除超时订单,每天检查一次
    """
    delete_list = []
    utc_now = datetime.datetime.now().astimezone(pytz.utc)
    orders = Orders.objects.filter(pay_status=0, order_status=0).all()
    for order_obj_item in orders:
        if order_obj_item.created_at + datetime.timedelta(hours=24) <= utc_now:
            delete_list.append(order_obj_item.id)
            order_obj_item.delete()
    data = {
        'orders': delete_list,
        'status': 1
    }
    return json.dumps(data)


@shared_task(name='delete_expired_order')
def delete_expired_order():
    """
    定时检查db中订单状态，如果订单过期，删除对应的proxy，每10天检查一次
    """
    utc_now = datetime.datetime.now().astimezone(pytz.utc)
    orders = Orders.objects.filter(pay_status=1, order_status=4).all()  # 已支付，已发货
    ret_orders = []
    for order_obj_item in orders:
        if order_obj_item.expired_at <= utc_now:
            ret_orders.append(order_obj_item.id)
            proxy = Proxy.objects.filter(order_id=order_obj_item.id).first()
            if proxy:
                client = KaxyClient(proxy.server_ip)
                client.del_user(proxy.username)
                proxy.delete()
                order_obj_item.order_status = 3
                order_obj_item.save()
            order_obj_item.delete()
    data = {
        'orders': ret_orders,
        'status': 1
    }
    return json.dumps(data)


@shared_task(name='delete_expired_order')
def delete_expired_order():
    """
    定时检查db中订单状态，如果订单过期，删除对应的proxy，每10天检查一次
    """
    utc_now = datetime.datetime.now().astimezone(pytz.utc)
    orders = Orders.objects.filter(pay_status=1, order_status=4).all()  # 已支付，已发货
    ret_orders = []
    for order_obj_item in orders:
        if order_obj_item.expired_at <= utc_now:
            ret_orders.append(order_obj_item.id)
            proxy = Proxy.objects.filter(order_id=order_obj_item.id).first()
            if proxy:
                client = KaxyClient(proxy.server_ip)
                client.del_user(proxy.username)
                proxy.delete()
                order_obj_item.order_status = 3
                order_obj_item.save()
            order_obj_item.delete()
    data = {
        'orders': ret_orders,
        'status': 1
    }
    return json.dumps(data)


@shared_task(name='delivery_order')
def delivery_order(order_pk=None, order_id=None):
    if order_id:
        order = Orders.objects.filter(order_id=order_id).first()
        if order:
            order_pk = order.id
    if order_pk:
        filter_dict = {
            'id': order_pk,
            'pay_status': 1,
        }
        create_proxy(filter_dict)
