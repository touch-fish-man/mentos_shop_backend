from __future__ import absolute_import
import datetime
import json
import time

import pytz
from celery.schedules import crontab
from apps.orders.models import Orders
from apps.orders.services import create_proxy
from apps.products.models import Variant
from apps.proxy_server.models import Proxy
from apps.users.models import User
from apps.users.services import send_via_sendgrid, send_email_via_mailgun
from django.conf import settings
from django.core.mail import send_mail
from apps.utils.kaxy_handler import KaxyClient
from celery import shared_task
from django.core.cache import cache

from apps.utils.shopify_handler import SyncClient


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


@shared_task(name='update_shopify_product')
def update_shopify_product(product_id=None,action=None):
    """
    更新shopify产品
    """
    shop_url = settings.SHOPIFY_SHOP_URL
    api_key = settings.SHOPIFY_API_KEY
    api_scert = settings.SHOPIFY_API_SECRET
    private_app_password = settings.SHOPIFY_APP_KEY
    cache_client = cache.client.get_client()
    shopify_client = SyncClient(shop_url, api_key, api_scert, private_app_password)
    cache_key = 'shopify_product'
    if action == 'delete':
        cache_client.hdel(cache_key, product_id)
    else:  # update or create
        product_dict=[]
        for _ in range(3):
            try:
                product_dict = shopify_client.get_products(format=True,product_id=product_id)
                break
            except Exception as e:
                print(e)
                time.sleep(1)
        for product in product_dict:
            cache_client.hset('shopify_product', product['id'], json.dumps(product))
            for variant in product['variants']:
                variant_id = variant['shopify_variant_id']
                price = variant['variant_price']
                Variant.objects.filter(shopify_variant_id=variant_id).update(variant_price=price)
    collection_data = shopify_client.sync_product_collections()
    time.sleep(1)
    tag_data = shopify_client.sync_product_tags()


@shared_task(name='delete_old_order')
def delete_old_order():
    """
    删除expired_at 1个月前的订单
    """
    delete_list = []
    utc_now = datetime.datetime.now().astimezone(pytz.utc)
    orders = Orders.objects.filter(expired_at__lt=utc_now - datetime.timedelta(days=15)).all()
    for order_obj_item in orders:
        oerder_id = order_obj_item.id
        if Proxy.objects.filter(order_id=oerder_id).exists():
            continue
        delete_list.append(order_obj_item.id)
        order_obj_item.delete()
    data = {
        'orders': delete_list,
        'status': 1
    }
    return json.dumps(data)
