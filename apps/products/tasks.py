import asyncio
import datetime
import json
import logging
import socket
import threading
import time
from urllib.parse import urlparse
import ssl
import requests
import urllib3
from aiohttp import ClientSession, ClientTimeout
from aiohttp_proxy import ProxyConnector
from celery import shared_task
from django.core import management
from django.utils import timezone
from django_celery_beat.models import PeriodicTask, IntervalSchedule
import os

from apps.orders.services import create_proxy
from apps.proxy_server.models import Proxy
from apps.proxy_server.models import Server
from apps.utils.kaxy_handler import KaxyClient
import certifi
from rich.console import Console
from rich.progress import Progress
import subprocess

os.environ['SSL_CERT_FILE'] = certifi.where()

# List of URLs to be checked
urls = ['http://httpbin.org/get', 'http://www.google.com', "https://icanhazip.com/", "https://jsonip.com/",
        "https://api.seeip.org/jsonip", "https://api.geoiplookup.net/?json=true"]
URLS = ['https://www.google.com', "https://global.bing.com/?setlang=en&cc=US", "https://checkip.amazonaws.com",
        'http://httpbin.org/get']
netloc_models = {
    "www.google.com": "google_delay",
    "global.bing.com": "bing_delay",
    "icanhazip.com": "icanhazip_delay",
    "jsonip.com": "jsonip_delay",
    "api.seeip.org": "seeip_delay",
    "api.geoiplookup.net": "geoiplookup_delay",
    "checkip.amazonaws.com": "amazon_delay",
    "httpbin.org": "httpbin_delay",
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
def reset_proxy_fn(order_id, username):
    lock_id = "reset_proxy_" + str(order_id)
    with cache.lock(lock_id):
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
        filter_dict = {"id": order_id, "pay_status": 1}
        re_create_ret, msg, ret_proxy_list = create_proxy(filter_dict)
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


lock = threading.Lock()


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
            logging.exception(f"Error checking {url}: {e}")  # Replace with your preferred logging
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


sslcontext = ssl.create_default_context(cafile=certifi.where())


async def fetch_using_proxy(url, proxy):
    proxy_url = urlparse(proxy)
    try:
        connector = ProxyConnector.from_url(proxy)
    except:
        logging.error(f"Error parsing proxy URL: {proxy}")
        return url, proxy, 99999, False
    if ".255:" in proxy:
        return url, proxy, 99999, False
    try:
        start_time = time.perf_counter()
        async with ClientSession(connector=connector, timeout=ClientTimeout(total=10)) as session:
            async with session.get(url, ssl=sslcontext) as response:
                await response.read()
                latency = round((time.perf_counter() - start_time) * 1000)  # Latency in milliseconds
                # logging.info(f'URL: {url}, Proxy: {proxy}, Latency: {latency}, Status: {response.status}')
                if response.ok and response.status == 200:
                    return url, proxy, latency, True
                else:
                    return url, proxy, 99999, False
    except asyncio.TimeoutError as e:
        logging.info(f'Error. URL: {url}, Proxy: {proxy}; request timeout')
        latency = 99999
        return url, proxy, latency, False
    except Exception as e:
        logging.info(f'Error. URL: {url}, Proxy: {proxy}; Error: {e}', exc_info=True)
        latency = 99999
        return url, proxy, latency, False
    finally:
        # 确保在结束时关闭连接器
        await connector.close()


def get_proxies(order_id=None, id=None, status=None):
    filter_dict = {}
    if order_id is not None:
        filter_dict['order_id'] = order_id
    if id is not None:
        filter_dict['id'] = id
    if status is not None:
        filter_dict['status'] = status
    proxies = Proxy.objects.filter(**filter_dict).values_list('ip', 'port', 'username', 'password', 'id')
    proxies_dict = {}
    for p in proxies:
        p = list(p)
        proxy_str = f"http://{p[2]}:{p[3]}@{p[0]}:{p[1]}"
        proxies_dict[proxy_str] = p[4]
    if order_id == None and id == None and status == None:
        proxies_list = sorted(list(proxies_dict.keys()))
        with open('/opt/mentos_shop_backend/logs/http_user_pwd_ip_port.txt', 'w') as f:
            f.write('\n'.join(proxies_list))
    return proxies_dict


class AsyncCounter:
    def __init__(self):
        self.count = 0
        self._lock = asyncio.Lock()

    async def increment(self):
        async with self._lock:
            self.count += 1
            return self.count


async def check_proxies_from_db(order_id):
    proxies = get_proxies(order_id=order_id)  # 假设这是您之前定义的函数
    semaphore = asyncio.Semaphore(800)
    fail_list = set()
    success_updates = {}
    total_count = len(proxies)
    progress_counter = AsyncCounter()

    async def bounded_fetch(url, proxy, progress, task_id, total, counter):
        async with semaphore:
            result = await fetch_using_proxy(url, proxy)
            current_count = await counter.increment()
            progress.update(task_id, advance=1)
            if current_count / total * 100 % 10 == 0:
                logging.info(f"检查代理进度:{current_count}/{total}")
            return result

    with Progress() as progress:
        task_id = progress.add_task("[green]检测代理中...", total=len(proxies) * len(URLS))
        tasks = [bounded_fetch(url, proxy, progress, task_id, len(proxies) * len(URLS), progress_counter)
                 for proxy in proxies.keys() for url in URLS]

        for task in asyncio.as_completed(tasks):
            url, proxy, latency, success = await task
            id = proxies.get(proxy)
            model_name = netloc_models.get(urlparse(url).netloc, None)
            if model_name:
                if id not in success_updates:
                    success_updates[id] = {}
                success_updates[id].update({model_name: latency})
                if len(success_updates[id]) == len(URLS):
                    proxy = Proxy.objects.filter(id=id).first()
                    if sum(success_updates[id].values()) == 99999 * len(URLS):
                        fail_list.add(id)
                    if proxy:
                        for field, value in success_updates[id].items():
                            setattr(proxy, field, value)
                        proxy.save()

    fail_list = sorted(list(fail_list))
    return fail_list, total_count


@shared_task(name='check_proxy_status')
def check_proxy_status(order_id=None):
    """
    检查代理状态,每4个小时检查一次
    """
    logging.info("==========check_proxy_status==========")
    s = time.time()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    fail_list, total_count = loop.run_until_complete(check_proxies_from_db(order_id))
    loop.close()
    e = time.time()
    print(f"检查代理状态,总数:{total_count},失败数:{len(fail_list)},耗时:{e - s}s")
    return {"total_count": total_count, "status": 1, "cost_time": e - s, "fail_list": fail_list}


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
    # redis队列
    cache.scan_iter("del_user_list")
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


@shared_task(name='add_blacklist')
def add_blacklist(server_groups, domains):
    """
    添加黑名单
    """
    server_groups = server_groups.split(',')
    from apps.proxy_server.models import ServerGroupThrough
    server_ids = ServerGroupThrough.objects.filter(server_group_id__in=server_groups).values_list('server_id',
                                                                                                  flat=True)
    server_list = Server.objects.filter(id__in=server_ids).values_list('ip', flat=True)
    for server in server_list:
        kaxy_client = KaxyClient(server)
        domains_s = domains.split(',')
        kaxy_client.add_domain_blacklist(domains_s)
    return {"status": 1}


@shared_task(name='remove_blacklist')
def remove_blacklist(server_groups, domains):
    """
    移除黑名单
    """
    server_groups = server_groups.split(',')
    from apps.proxy_server.models import ServerGroupThrough
    server_ids = ServerGroupThrough.objects.filter(server_group_id__in=server_groups).values_list('server_id',
                                                                                                  flat=True)
    result_json = {}
    server_list = Server.objects.filter(id__in=server_ids).values_list('ip', flat=True)
    for server in server_list:
        kaxy_client = KaxyClient(server)
        domains_s = domains.split(',')
        kaxy_client.del_domain_blacklist(domains_s)
    return {"status": 1}


@shared_task(name='stock_return_task', autoretry_for=(Exception,), retry_kwargs={'max_retries': 7, 'countdown': 5})
def stock_return_task(ip_stock_ids, subnet):
    """
    代理库存归还
    """
    ids = ip_stock_ids.split(',')
    from apps.proxy_server.models import ProxyStock
    ret_dict = {}

    proxy_stocks = ProxyStock.objects.filter(id__in=ids).all()
    has_proxy = Proxy.objects.filter(subnet=subnet).all()
    acl_ids=[]
    proxy_ids = [p.id for p in has_proxy]
    for p in has_proxy:
        acl_ids.extend(p.acl_ids.split(',') if p.acl_ids else [])
    for proxy_stock in proxy_stocks:
        cache_key = f"stock_return_task_action_{proxy_stock.id}"
        cache_client = cache.client.get_client()
        with cache_client.lock(cache_key, timeout=60):
            if str(proxy_stock.acl_id) in acl_ids:
                logging.info(f"代理库存归还失败,库存被占用,库存ID:{proxy_stock.id},ACL_ID:{proxy_stock.acl_id},SUBNET:{subnet},占用的代理ID:{proxy_ids},占用的ACL_ID:{acl_ids}")
                ret_dict[proxy_stock.id] = 0
                ret_dict["status"] = 0
                ret_dict["msg"] = "库存被占用"
            else:
                proxy_stock.return_subnet(subnet)
                logging.info(f"代理库存归还成功,库存ID:{proxy_stock.id},ACL_ID:{proxy_stock.acl_id},SUBNET:{subnet}")
                ret_dict[proxy_stock.id] = 1
                ret_dict["status"] = 1
    return ret_dict


@shared_task(name='delete_proxy_task')
def delete_proxy_task(server_ip, username):
    """
    删除代理
    """
    delete_proxy = False
    delete_acl = False
    kaxy_client = KaxyClient(server_ip)
    try:
        kaxy_client.del_user(username)
        delete_proxy = True
    except Exception as e:
        pass

    try:
        kaxy_client.del_acl(username)
        delete_acl = True
    except Exception as e:
        pass
    return {"status": 1, "data": {"server_ip": server_ip, "username": username}, "delete_proxy": delete_proxy,
            "delete_acl": delete_acl}
