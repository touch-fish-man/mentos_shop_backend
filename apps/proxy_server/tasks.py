#!/usr/bin/env python
import datetime
import random
import string

import os
import sys
import requests
import time
from concurrent.futures import ThreadPoolExecutor

from init_env import *
from rich.console import Console
from rich.progress import track
import ipaddress
from apps.core.cache_lock import memcache_lock

console = Console()
from apps.proxy_server.models import Proxy, ProxyStock, ServerGroup, Server, AclGroup, ServerCidrThrough, \
    ServerGroupThrough, Cidr
from apps.orders.models import Orders
from apps.products.models import Variant, ProductTag, ProductTagRelation, Product
from apps.utils.kaxy_handler import KaxyClient
from apps.orders.services import create_proxy_by_id
import click
from apps.orders.tasks import delete_proxy_expired


@click.group()
def cli():
    pass


def is_ip_in_network(ip_str, network_str):
    ip = ipaddress.ip_address(ip_str)
    network = ipaddress.ip_network(network_str)
    return ip in network


@cli.command()
def fix_stock():
    """
    修复库存
    """
    for xxx in ProxyStock.objects.all():
        ppp = Proxy.objects.filter(ip_stock_id=xxx.id).all()
        if xxx.subnets:
            subnets = xxx.subnets.split(",")
            for p in ppp:
                if p.subnet in subnets:
                    subnets.remove(p.subnet)
            subnets.sort()
            cart_stock = len(subnets)
            xxx.available_subnets = ",".join(subnets)
            # print(xxx.available_subnets)
            if xxx.cart_stock != cart_stock:
                print("id: {} fix stock: {} -> {}".format(xxx.id, xxx.cart_stock, cart_stock))
                xxx.cart_stock = cart_stock
                xxx.available_subnets = ",".join(subnets)
                xxx.ip_stock = cart_stock * xxx.cart_step
                xxx.save()
    for x in Variant.objects.all():
        x.save()


@cli.command()
def clean_stock():
    """
    清理无效库存条目
    """
    used_stock_ids = []
    for va in Variant.objects.all():
        va.get_stock()
        used_stock_ids.extend(va.stock_ids)
    for xxx in ProxyStock.objects.all():
        ppp = Proxy.objects.filter(ip_stock_id=xxx.id).all()  # 没有发货数据
        if not ppp and not used_stock_ids.__contains__(xxx.id):
            print(xxx.id)
            xxx.delete()


def get_cidr(server_group):
    cidr_ids = []
    if server_group:

        server_ids = ServerGroupThrough.objects.filter(server_group_id=server_group.id).values_list('server_id',
                                                                                                    flat=True)
        cidr_ids = ServerCidrThrough.objects.filter(server_id__in=server_ids).values_list('cidr_id', flat=True)
        ip_count = Cidr.objects.filter(id__in=cidr_ids).values_list('ip_count', flat=True)
        return cidr_ids, ip_count
    else:
        return cidr_ids, []


def fix_cidr():
    # 查询所有产品
    for variant_obj in Variant.objects.all():
        servers = variant_obj.server_group.servers.all()
        acl_group = variant_obj.acl_group.id

        for server in servers:
            cidr_info = server.get_cidr_info()
            for cidr_i in cidr_info:
                ip_stock = cidr_i.get('ip_count')
                if not ProxyStock.objects.filter(variant_id=variant_obj.id, acl_group_id=acl_group,
                                                 cidr_id=cidr_i['id']).exists():
                    cart_stock = ip_stock // variant_obj.cart_step
                    porxy_stock = ProxyStock.objects.create(cidr_id=cidr_i['id'], acl_group_id=acl_group,
                                                            ip_stock=ip_stock, variant_id=variant_obj.id,
                                                            cart_step=variant_obj.cart_step,
                                                            cart_stock=cart_stock)
                    subnets = porxy_stock.gen_subnets()
                    porxy_stock.subnets = ",".join(subnets)
                    porxy_stock.available_subnets = porxy_stock.subnets
                    porxy_stock.save()
                    print("创建库存", porxy_stock.id)
                else:
                    porxy_stock = ProxyStock.objects.filter(variant_id=variant_obj.id, acl_group_id=acl_group,
                                                            cidr_id=cidr_i['id']).first()
                    if not porxy_stock.subnets:
                        subnets = porxy_stock.gen_subnets()
                        porxy_stock.subnets = ",".join(subnets)
                        porxy_stock.available_subnets = porxy_stock.subnets
                        porxy_stock.save()
                        print("更新库存", porxy_stock.id)
        variant_obj.save()


def fix_product():
    # 合并商品标签关系
    tag_dict = {}
    for product_tag in ProductTag.objects.all():
        if product_tag.tag_name not in tag_dict:
            tag_dict[product_tag.tag_name] = []
            tag_dict[product_tag.tag_name].append(product_tag.id)
        else:
            tag_dict[product_tag.tag_name].append(product_tag.id)
            tag_dict[product_tag.tag_name].sort()
    for relation in ProductTagRelation.objects.all():
        # 合并商品标签关系
        for tag_k, tag_v in tag_dict.items():
            if relation.product_tag_id in tag_v[1:]:
                relation.product_tag_id = tag_v[0]
                relation.save()
                print("合并商品标签关系", relation.id)
    # 删除多余商品标签
    for tag_k, tag_v in tag_dict.items():
        for tag_id in tag_v[1:]:
            ProductTag.objects.filter(id=tag_id).delete()
            print("删除多余商品标签", tag_id)


@cli.command()
def find_repeat():
    """
    查找重复发货代理
    """
    cnt = 0
    xxx = {}
    order_id = set()
    order_ = set()
    for ppp in Proxy.objects.all():
        key = "-".join((str(ppp.ip), str(ppp.ip_stock_id)))
        if key in xxx:
            print(ppp.id, ppp.subnet, ppp.ip_stock_id, ppp.order_id, xxx[key])
            order_.add((ppp.order_id, xxx[key]))
            order_id.add(ppp.order_id)
            cnt += 1
        else:
            xxx[key] = ppp.order_id
    print("重复发货代理数量", cnt)
    order_ = list(order_)
    # 根据第二个元素排序
    order_.sort(key=lambda x: x[1])
    for xi in order_:
        print(xi)


@cli.command()
def proxy_compare_order():
    """
    检查发货代理数量和订单数量是否一致
    """
    cnt = 0
    xxx = {}
    order_id = set()
    order_ = set()
    for ppp in Proxy.objects.all():
        if ppp.order_id in xxx:
            xxx[ppp.order_id] += 1
        else:
            xxx[ppp.order_id] = 1
        if not ppp.subnet:
            for s in ProxyStock.objects.filter(id=ppp.ip_stock_id).first().gen_subnets():
                if is_ip_in_network(ppp.ip, s):
                    ppp.subnet = s
                    ppp.save()
                    break
    for ooo in Orders.objects.all():
        if ooo.id in xxx:
            if xxx[ooo.id] != ooo.proxy_num:
                ppp = Proxy.objects.filter(order_id=ooo.id).first()
                username = ppp.username
                server_ip = ppp.server_ip
                # print(ooo.id, ooo.proxy_num, xxx[ooo.id], username, server_ip)
                print("订单id:{} 应发货代理数量:{} 实际发货代理数量:{} 用户名:{} 服务器ip:{}".format(ooo.id,
                                                                                                     ooo.proxy_num,
                                                                                                     xxx[ooo.id],
                                                                                                     username,
                                                                                                     server_ip))


@cli.command()
@click.option('-p', '--proxy', help='代理，格式：username:password@ip:port')
def check_proxy(proxy):
    """
    检测代理是否可用 代理格式：username:password@ip:port
    """
    status = False
    try:
        proxies = {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }
        response = requests.get('https://checkip.amazonaws.com', proxies=proxies, timeout=5)
        if response.status_code == 200:
            status = True
        else:
            status = False
    except Exception as e:
        print(e)
        status = False
    if status:
        print(f"{proxy} 可用")
    else:
        print(f"{proxy} 不可用")
    return status


def check_proxy_fn(proxy):
    """
    检测代理是否可用 代理格式：username:password@ip:port
    """
    status = False
    try:
        proxies = {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }
        response = requests.get('https://checkip.amazonaws.com', proxies=proxies, timeout=5)
        if response.status_code == 200:
            status = True
        else:
            status = False
    except Exception as e:
        print(e)
        status = False
    if status:
        print(f"{proxy} 可用")
    else:
        print(f"{proxy} 不可用")
    return status


@cli.command()
def check_all_proxy():
    """
    检测所有代理是否可用
    """
    from apps.proxy_server.tasks import check_proxy_status
    check_proxy_status.delay()

@cli.command()
@click.option('--server_ip', default=None, help='服务器IP')
def change_proxy(server_ip):
    """
    修改指定服务器的失效代理
    """
    kc = KaxyClient(server_ip)
    user_dict = {}
    with console.status("[bold green]修改代理中...", spinner="monkey"):
        for x in Proxy.objects.filter(server_ip=server_ip, status=0).all():
            if x.username not in user_dict:
                user_dict[x.username] = set()
            user_dict[x.username].add(x.subnet)
        for u, sub_ in user_dict.items():
            need_update = set()
            for s in sub_:
                resp_json = kc.create_user_by_prefix(u, s)
                for proxy_i in resp_json["data"]["proxy_str"]:
                    ip, port, user, password = proxy_i.split(":")
                    need_update.add((ip, user, password))
            for ip, user, password in need_update:
                Proxy.objects.filter(username=user, ip=ip).update(password=password, status=1)
                print(ip, user, password)


@cli.command()
def flush_access_cache():
    """
    清理访问日志
    """
    for s in track(Server.objects.all(), description="清理访问日志中..."):
        try:
            s_c = KaxyClient(s.ip)
            print(s_c.flush_access_log().text)
        except Exception as e:
            pass


@cli.command()
def check_server():
    """
    检查服务器状态
    """
    from apps.proxy_server.tasks import check_server_status, delete_user_from_server
    check_server_status.apply()


@cli.command()
def delete_expired():
    """
    删除过期代理
    """
    delete_proxy_expired()


@cli.command()
@click.option('--detial', "-d", is_flag=True, help='是否打印详情')
def check_order_proxy(detial):
    """
    检查订单代理是否可用
    """
    # 获取有效订单
    with console.status("[bold green]查询订单代理中...", spinner="dots"):
        orders = Orders.get_vaild_orders()
    csv_data = []
    for order in track(orders):
        get_proxies_failed = order.get_proxies_failed()
        # print("订单id,代理失效数量,代理总数量,用户名")
        if get_proxies_failed > 0:
            # print("{},{},{},{}".format(order.id, get_proxies_failed, order.proxy_num, order.username))
            csv_data_line = "{},{},{},{}".format(order.id, get_proxies_failed, order.proxy_num, order.username)
            csv_data.append(csv_data_line)
            if detial:
                order.pretty_print({"代理失效数量": get_proxies_failed})
    if len(csv_data) > 0:
        csv_data.insert(0, "订单id,代理失效数量,代理总数量,用户名")
        with open("/opt/mentos_shop_backend/logs/check_order_proxy.csv", "w") as f:
            f.write("\n".join(csv_data))
            print("检测完成: 结果已保存到 /opt/mentos_shop_backend/logs/check_order_proxy.csv")


@cli.command()
@click.option('--log_type', default="server",
              help='日志类型 server:服务器日志 error:错误日志 access:访问日志 celery:celery日志')
def logs(log_type="server"):
    """
    显示日志
    """
    if log_type == "server":
        with open("logs/server.log", "r") as f:
            data = f.readlines()
    elif log_type == "error":
        with open("logs/error.log", "r") as f:
            data = f.readlines()
    elif log_type == "access":
        with open("logs/access.log", "r") as f:
            data = f.readlines()
    elif log_type == "celery":
        with open("logs/celery_work.log", "r") as f:
            data = f.readlines()
    print("".join(data[-500:]))


@cli.command()
@click.option('-d', default=0, help='是否去重')
@click.option('-s','--status', default=None ,help='状态')
@click.option('-u', "--username", default=None, help='用户名')
@click.option('-o', "--order_id", default=None, help='订单id')
@click.option('-ip', "--server_ip", default=None, help='服务器ip')
def export_all_proxy(d, username, order_id, server_ip,status):
    """
    导出所有代理
    """
    proxies = []
    proxies_2 = []
    ip = {}
    filter = {}
    if status is not None:
        filter["status"] = status
    if username is not None:
        filter["username"] = username
    if order_id is not None:
        filter["order_id"] = order_id
    if server_ip is not None:
        filter["server_ip"] = server_ip
    for i in Proxy.objects.filter(**filter).all():
        # 检测代理是否可用
        if d == 0:
            proxy_str = f"{i.username}:{i.password}@{i.ip}:{i.port}"
            proxy_str_2 = f"{i.ip}:{i.port}:{i.username}:{i.password}"
            proxies.append(proxy_str)
            proxies_2.append(proxy_str_2)
        else:
            if i.ip not in ip:
                ip[i.ip] = 1
                proxy_str = f"{i.username}:{i.password}@{i.ip}:{i.port}"
                proxy_str_2 = f"{i.ip}:{i.port}:{i.username}:{i.password}"
                proxies.append(proxy_str)
                proxies_2.append(proxy_str_2)
    with open("/opt/mentos_shop_backend/logs/user_pwd_ip_port.txt", "w") as f:
        f.write("\n".join(proxies))
    with open("/opt/mentos_shop_backend/logs/http_user_pwd_ip_port.txt", "w") as f:
        proxies_1 = [f"http://{i}" for i in proxies]
        f.write("\n".join(sorted(proxies_1)))
    with open("/opt/mentos_shop_backend/logs/ip_port_user_pwd.txt", "w") as f:
        f.write("\n".join(proxies_2))


@cli.command()
def sql():
    """
    进入数据库
    """
    os.system("python /opt/mentos_shop_backend/manage.py dbshell")


@cli.command()
@click.option('--url', default=None, help='url')
@click.option('--proxy', default=None, help='代理')
def check_delay(url, proxy):
    """
    检查延迟
    """
    if proxy:
        proxy = ["http://" + proxy]
    else:
        proxy_objs = Proxy.objects.filter(status=1).all()
        proxy = []
        for proxy_obj in proxy_objs:
            proxy.append("http://" + proxy_obj.get_proxy_str())
    if url:
        try:
            for p in proxy:
                resp = requests.get(url, proxies={"http": p})
                print(f"{p} {resp.elapsed.total_seconds()}")
        except Exception as e:
            print(f"{p} {e}")
    else:
        print("请输入url")


@cli.command()
def update():
    """
    更新代码重新部署
    """
    os.system("git pull")
    os.system("supervisorctl restart all")


cli_all = click.CommandCollection(sources=[cli])
if __name__ == '__main__':
    cli_all()
