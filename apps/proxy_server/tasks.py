import datetime
import logging
import os
import socket
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
from django.views.decorators.cache import cache_page

from apps.utils.kaxy_handler import KaxyClient
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from django.core.cache import cache


@shared_task(name='check_server_status')
def check_server_status(faild_count=5):
    """
    检查服务器状态,每10分钟检查一次
    """
    servers = Server.objects.filter(faild_count__lt=faild_count).all()
    faild_list = []
    for server in servers:
        try:
            kaxy_client = KaxyClient(server.ip)
            if kaxy_client.status:
                server.server_status = 1
                server.faild_count = 0
            else:
                server.server_status = 0
                server.faild_count += 1
                faild_list.append(server.ip)
        except Exception as e:
            server.server_status = 0
            server.faild_count += 1
            faild_list.append(server.ip)
        print(server.ip, server.server_status)
        server.save()
        if server.faild_count >= 5:
            # 服务器连续5次检查失败
            pass
    data = {
        "faild_list": faild_list,
        "status": 1
    }
    return json.dumps(data)


@shared_task(name='reset_proxy')
def reset_proxy_fn(order_id, username, server_ip):
    ret_json = {}
    logging.info("==========create_proxy_by_id {}==========".format(order_id))
    delete_proxy_list = []
    server_ip_username = Proxy.objects.filter(order_id=order_id).values_list('server_ip', 'username').distinct()
    for server_ip, username in server_ip_username:
        server_exists = Server.objects.filter(ip=server_ip).exists()
        if not server_exists:
            continue
        kaxy_client = KaxyClient(server_ip)
        kaxy_client.del_user(username)
    re_create_ret, ret_proxy_list, msg = create_proxy_by_id(order_id)
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


@cache_page(60 * 60 * 2)
def is_port_open(proxy_port):
    """
    获取端口状态
    """
    ip, port = proxy_port.split(':')
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)  # 设置超时，例如1秒
    try:
        s.connect((ip, port))
        s.close()
        return True
    except socket.error:
        return False


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
    port_open = True
    delay = 99999
    try:
        proxies = {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }
        ip_port = proxy.split('@')[1]
        # port_open = is_port_open(ip_port)
        if port_open:
            s_time = time.time()
            response = requests.get('https://checkip.amazonaws.com', proxies=proxies, timeout=5, verify=False)
            e_time = time.time()
            delay = int((e_time - s_time) * 1000)
            # logging.warning(response.status_code)
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
            s_time = time.time()
            response = requests.get('https://www.bing.com', proxies=proxies, timeout=5, verify=False)
            e_time = time.time()
            delay = int((e_time - s_time) * 1000)
            if response.status_code == 200:
                status = True
            else:
                status = False
        except Exception as e:
            status = False
    if not port_open:
        status = False
    proxy_obj = Proxy.objects.filter(id=id).first()
    if proxy_obj:
        proxy_obj.status = status
        proxy_obj.delay = delay
        proxy_obj.save()
    return proxy, status, id, delay


@shared_task(name='check_proxy_status')
def check_proxy_status(order_id=None):
    """
    检查代理状态,每4个小时检查一次
    """
    # 获取所有代理
    if order_id:
        proxies = list(Proxy.objects.filter(order_id=order_id).all())
    else:
        proxies = list(Proxy.objects.all())
    if order_id is None:
        # 获取所有状态为0的服务器IP
        offline_server_ips = set(Server.objects.filter(server_status=0).values_list('ip', flat=True))
    else:
        offline_server_ips = []

    to_update_ids = []
    proxy_data = []

    for p in proxies:
        if p.server_ip in offline_server_ips:
            to_update_ids.append(p.id)
        else:
            proxy_data.append((p.get_proxy_str(), p.id))

    # 批量更新代理状态为False
    if to_update_ids:
        Proxy.objects.filter(id__in=to_update_ids).update(status=False)

    # 使用线程池并发检查代理状态
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(lambda x: check_proxy(x[0], x[1]), proxy_data)
    ret_json = {}
    faild_list = []
    for proxy, status, id,delay in results:
        if not status:
            faild_list.append((proxy, id,delay))
    ret_json['code'] = 200
    ret_json['message'] = 'success'
    ret_json['faild_list'] = faild_list
    return ret_json


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


@shared_task(name='delete_user_from_server')
def delete_user_from_server(server_ip=None, username=None):
    if server_ip and username:
        if Server.objects.filter(ip=server_ip, server_status=1).exists():  # 服务器在线
            try:
                kaxy_client = KaxyClient(server_ip)
                if kaxy_client.status:
                    kaxy_client.del_user(username)
                    kaxy_client.del_acl(username)
            except Exception as e:
                pass
        # cache.delete("del_user_list", server_ip + '_' + username)
    else:
        del_user_list = cache.hgetall("del_user_list")
        for server_user, cnt in del_user_list.items():
            server, user = server_user.split('_')
            if Server.objects.filter(ip=server_ip, server_status=1).exists():  # 服务器在线
                kaxy_client = KaxyClient(server)
                kaxy_client.del_user(user)
                kaxy_client.del_acl(user)
        cache.delete("del_user_list")
