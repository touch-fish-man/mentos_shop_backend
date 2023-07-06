import datetime
import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor

import requests
from django.core import management
from django.utils import timezone

from apps.proxy_server.models import Server, ProxyStock
import json
import time

from django_celery_beat.models import PeriodicTask, IntervalSchedule

from apps.orders.services import create_proxy_by_id
from apps.proxy_server.models import Proxy
from celery import shared_task

from apps.utils.kaxy_handler import KaxyClient


@shared_task(name='check_server_status')
def check_server_status():
    """
    检查服务器状态,每10分钟检查一次
    """
    servers = Server.objects.filter(faild_count__lt=5).all()
    for server in servers:
        kaxy_client = KaxyClient(server.ip)
        try:
            resp = kaxy_client.get_server_info()
            if resp.status_code == 200:
                server.server_status = 1
                server.faild_count = 0
            else:
                server.server_status = 0
                server.faild_count += 1
        except Exception as e:
            server.server_status = 0
            server.faild_count += 1
        server.save()
        if server.faild_count >= 5:
            # 服务器连续5次检查失败
            pass
    print('check_server_status done at %s' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


@shared_task(name='reset_proxy')
def reset_proxy_fn(order_id, username, server_ip):
    ret_json = {}
    logging.info("==========create_proxy_by_id {}==========".format(order_id))
    delete_proxy_list = []
    kaxy_client = KaxyClient(server_ip)
    kaxy_client.del_user(username)
    re_create_ret, ret_proxy_list,msg = create_proxy_by_id(order_id)
    if re_create_ret:
        new_proxy = Proxy.objects.filter(username=username).all()
        for p in new_proxy:
            if p.id not in ret_proxy_list and len(ret_proxy_list) > 0:
                p.delete()
        ret_json['code'] = 200
        ret_json['message'] = 'success'
        ret_json['data'] = {}
        ret_json['data']['delete_proxy_list'] = delete_proxy_list
        ret_json['data']['order_id'] = order_id
        ret_json['data']['re_create'] = re_create_ret
        logging.info("==========create_proxy_by_id success==========")
        return ret_json
    else:
        ret_json['code'] = 500
        ret_json['message'] = msg
        ret_json['data'] = {}
        ret_json['data']['re_create'] = re_create_ret
        ret_json['data']['order_id'] = order_id
        logging.info("==========create_proxy_by_id faild==========")
        return ret_json


@shared_task(name='delete_proxy_by_id')
def delete_proxy_by_id(id):
    pass


lock = threading.Lock()


@shared_task(name='delete_user_from_server')
def delete_user_from_server(server_ip, username, subnet, ip_stock_id):
    if Proxy.objects.filter(username=username).count() == 0:
        kax_client = KaxyClient(server_ip)
        kax_client.del_user(username)
        kax_client.del_acl(username)
        with lock:
            stock = ProxyStock.objects.filter(id=ip_stock_id).first()
            # 归还子网,归还库存
            if stock:
                if Proxy.objects.filter(subnet=subnet, ip_stock_id=stock.id).all().count() == 0:
                    stock.return_subnet(subnet)
                    stock.return_stock()
                    from apps.products.models import Variant
                    # 更新库存
                    variant = Variant.objects.filter(id=stock.variant_id).first()
                    if variant:
                        variant.save()


def create_proxy_task(order_id, username, server_ip):
    # 创建一次性celery任务，立即执行，执行完毕后删除
    interval = IntervalSchedule.objects.get_or_create(every=1, period=IntervalSchedule.SECONDS)[0]
    # 删除已有且已过期的任务
    PeriodicTask.objects.filter(name=f'重置代理_{order_id}', one_off=True, expires__lte=timezone.now()).delete()

    PeriodicTask.objects.get_or_create(
        name=f'重置代理_{order_id}',
        task='reset_proxy',
        args=json.dumps([order_id, username, server_ip]),
        interval=interval,
        one_off=True,
        expires=timezone.now() + datetime.timedelta(seconds=70)
    )

def check_proxy(proxy, id):
    status = True
    try:
        proxies = {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }
        response = requests.get('https://checkip.amazonaws.com', proxies=proxies, timeout=5, verify=False)
        if response.status_code == 200:
            status = True
        else:
            status = False
    except Exception as e:
        status = False
    if not status:
        try:
            proxies = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }
            response = requests.get('https://www.bing.com', proxies=proxies, timeout=5, verify=False)
            if response.status_code == 200:
                status = True
            else:
                status = False
        except Exception as e:
            status = False
    proxy_obj = Proxy.objects.filter(id=id).first()
    if proxy_obj:
        proxy_obj.status = status
        proxy_obj.save()
    return status
@shared_task(name='check_proxy_status')
def check_proxy_status():
    """
    检查代理状态,每4个小时检查一次
    """
    proxies = Proxy.objects.all()
    ids = []
    proxy_strs = []
    for p in proxies:
        server_ip = p.server_ip
        if Server.objects.filter(ip=server_ip,server_status=0).count() > 0:
            try:
                Proxy.objects.filter(id=p.id).update(status=False)
            except Exception as e:
                pass
            continue
        ids.append(p.id)
        proxy_strs.append(p.get_proxy_str())

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(lambda x: check_proxy(x[0], x[1]), zip(proxy_strs, ids))

@shared_task(name="cleanup_sessions")
def cleanup():
    """Cleanup expired sessions by using Django management command."""
    management.call_command("clearsessions", verbosity=0)
@shared_task(name='flush_access_log')
def clear_access_log():
    """
    清理访问日志,每天凌晨1点清理
    """
    for s in Server.objects.all():
        try:
            s_c = KaxyClient(s.ip)
            print(s_c.flush_access_log().text)
        except Exception as e:
            pass