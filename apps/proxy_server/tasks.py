import asyncio
import datetime
import json
import logging
import socket
import threading
import time
from urllib.parse import urlparse

import requests
import urllib3
from aiohttp import ClientSession, ClientTimeout
from aiohttp_proxy import ProxyConnector
from celery import shared_task
from django.core import management
from django.utils import timezone
from django.views.decorators.cache import cache_page
from django_celery_beat.models import PeriodicTask, IntervalSchedule

from apps.orders.services import create_proxy_by_id
from apps.proxy_server.models import Proxy
from apps.proxy_server.models import Server
from apps.utils.kaxy_handler import KaxyClient

# List of URLs to be checked
urls = ['http://httpbin.org/get', 'http://www.google.com', "https://icanhazip.com/", "https://jsonip.com/",
        "https://api.seeip.org/jsonip", "https://api.geoiplookup.net/?json=true"]
URLS = ['http://www.google.com', "https://bing.com", "https://checkip.amazonaws.com"]
netloc_models = {
    "www.google.com": "google_delay",
    "bing.com": "bing_delay",
    "icanhazip.com": "icanhazip_delay",
    "jsonip.com": "jsonip_delay",
    "api.seeip.org": "seeip_delay",
    "api.geoiplookup.net": "geoiplookup_delay",
    "checkip.amazonaws.com": "amazon_delay",
}
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


check_site_list = {
    "amazon": "https://checkip.amazonaws.com",
    # "bing": "https://www.bing.com",
}


def check_proxy(proxy, id):
    proxy_connect_faild = False

    def check_site(url):
        try:
            s_time = time.time()
            response = requests.get(url, proxies=proxies, timeout=5, verify=False)
            delay = int((time.time() - s_time) * 1000)
            return response.status_code == 200, delay
        except requests.exceptions.ProxyError:
            proxy_connect_faild = True
            return False, 99999
        except Exception as e:
            print(f"Error checking {url}: {e}")  # Replace with your preferred logging
            return False, 99999

    proxies = {
        'http': f'http://{proxy}',
        'https': f'http://{proxy}'
    }

    proxy_obj = Proxy.objects.filter(id=id).first()
    if proxy_obj:
        overall_status = False
        for site_name, site_url in check_site_list.items():
            if not proxy_connect_faild:
                status, delay = check_site(site_url)
            else:
                status, delay = False, 99999
            if hasattr(proxy_obj, f"{site_name}_delay"):
                setattr(proxy_obj, f"{site_name}_delay", delay)  # Dynamically set the delay attribute
            if status:
                overall_status = True
        proxy_obj.status = overall_status
        proxy_obj.save()

    return proxy, overall_status, id, delay


def read_proxies(proxy_file, batch_size=100):
    with open(proxy_file, 'r') as file:
        batch = []
        for line in file:
            if line.strip():
                batch.append(line.strip())
                if len(batch) == batch_size:
                    yield batch
                    batch = []
        if batch:
            yield batch


async def fetch_using_proxy(url, proxy):
    try:
        # 解析代理URL以获取用户名和密码
        proxy_url = urlparse(proxy)
        connector = ProxyConnector.from_url(proxy)
        start_time = time.perf_counter()
        async with ClientSession(connector=connector, timeout=ClientTimeout(total=5)) as session:
            async with session.get(url, ssl=False) as response:
                await response.read()
                latency = round((time.perf_counter() - start_time) * 1000)  # Latency in milliseconds
                logging.info(f'URL: {url}, Proxy: {proxy}, Latency: {latency}, Status: {response.status}')
                if response.ok and response.status == 200:
                    return url, proxy, latency, True
                else:
                    return url, proxy, 9999999, False
    except Exception as e:
        logging.info(f'Error. URL: {url}, Proxy: {proxy}; Error: {e}')
        latency = 9999999
        return url, proxy, latency, False


def get_proxies(order_id=None, id=None, status=None):
    filter_dict = {}
    if order_id is not None:
        filter_dict['order_id'] = order_id
    if id is not None:
        filter_dict['id'] = id
    if status is not None:
        filter_dict['status'] = status
    proxies = Proxy.objects.filter(**filter_dict).all()
    proxies_dict = {f'http://{p.get_proxy_str()}': p.id for p in proxies}

    return proxies_dict


async def check_proxies_from_db(order_id):
    proxies = get_proxies(order_id=order_id)
    tasks = [fetch_using_proxy(url, proxy) for proxy in proxies.keys() for url in URLS]
    results = await asyncio.gather(*tasks)
    for url, proxy, latency, success in results:
        id=proxies.get(proxy)
        if success:
            proxy_obj = Proxy.objects.filter(id=id).first()
            if proxy_obj:
                model_name = netloc_models.get(urlparse(url).netloc, None)
                if model_name and hasattr(proxy_obj, model_name):
                    setattr(proxy_obj, model_name, latency)
                    proxy_obj.save()


@shared_task(name='check_proxy_status')
def check_proxy_status(order_id=None):
    """
    检查代理状态,每4个小时检查一次
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(check_proxies_from_db(order_id))
    return result


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
