import copy
import datetime
import random
import string
from pprint import pprint

import pytz
from faker import Faker
import os
import sys
import requests
import time
from concurrent.futures import ThreadPoolExecutor

from init_env import *
from rich.console import Console
import ipaddress

console = Console()
from apps.proxy_server.models import Proxy, ProxyStock, ServerGroup, Server, AclGroup, ServerCidrThrough, \
    ServerGroupThrough, Cidr, Acls, CidrAclThrough, AclGroupThrough, ProductStock
from apps.orders.models import Orders
from apps.products.models import Variant, ProductTag, ProductTagRelation
from apps.utils.kaxy_handler import KaxyClient
from apps.products.services import add_product_other


def is_ip_in_network(ip_str, network_str):
    ip = ipaddress.ip_address(ip_str)
    network = ipaddress.ip_network(network_str)
    return ip in network


# 库存修复
def fix_stock():
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
                print(xxx.cart_stock, cart_stock, xxx.id)
                xxx.cart_stock = cart_stock
                xxx.available_subnets = ",".join(subnets)
                xxx.ip_stock = cart_stock * xxx.cart_step
                xxx.save()
    for x in Variant.objects.all():
        x.save()


# 删除多余库存数据
def delete_stock():
    for xxx in ProxyStock.objects.all():
        ppp = Proxy.objects.filter(ip_stock_id=xxx.id).all()  # 没有发货数据
        va = Variant.objects.filter(id=xxx.variant_id).first()  # 没有商品数据
        if not ppp and not va:
            print(xxx.id)
            xxx.delete()


# delete_stock()
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


# fix_cidr()
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


# fix_product()
def classify_stock():
    proxy_stock_dict = {}
    for sss in ProxyStock.objects.all():
        # 根据cidr_id,acl_group_id,car_step合并库存
        key = "-".join((str(sss.cidr_id), str(sss.acl_group_id), str(sss.cart_step)))
        if key not in proxy_stock_dict:
            proxy_stock_dict[key] = []
            proxy_stock_dict[key].append(sss.id)
        else:
            proxy_stock_dict[key].append(sss.id)
            proxy_stock_dict[key].sort()
    for k, v in proxy_stock_dict.items():
        for id in v[1:]:
            # 修改proxy表中的库存id
            Proxy.objects.filter(ip_stock_id=id).update(ip_stock_id=v[0])
            # 删除多余库存
            ProxyStock.objects.filter(id=id).delete()
            print("删除多余库存", id)


def find_repeat():
    # 查找重复发货代理
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
    print(cnt)
    order_ = list(order_)
    # 根据第二个元素排序
    order_.sort(key=lambda x: x[1])
    for xi in order_:
        print(xi)


# find_repeat()
def proxy_compare_order():
    # 比较发货代理和订单
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
                print(ooo.id, ooo.proxy_num, xxx[ooo.id], username, server_ip)


def check_proxy(proxy):
    try:
        proxies = {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }
        response = requests.get('https://checkip.amazonaws.com', proxies=proxies, timeout=5)
        if response.status_code == 200:
            return True
        else:
            return False
    except Exception as e:
        print(e)
        return False


def check_all_proxy():
    # 检测所有代理是否可用
    proxies = []
    for i in Proxy.objects.all():
        # 检测代理是否可用
        proxy_str = f"{i.username}:{i.password}@{i.ip}:{i.port}"
        proxies.append(proxy_str)
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(check_proxy, proxies)
    invalid_proxy = [proxy for proxy, result in zip(proxies, results) if result]
    with open("invalid_proxy.txt", "w") as f:
        f.write("\n".join(invalid_proxy))


def change_proxy():
    # 修改代理
    kc = KaxyClient("112.75.252.6")
    user_dict = {}
    for x in Proxy.objects.filter(server_ip="112.75.252.6", status=0).all():
        if x.username not in user_dict:
            user_dict[x.username] = set()
        user_dict[x.username].add(x.subnet)
    for u, sub_ in user_dict.items():
        need_update = set()
        for s in sub_:
            resp = kc.create_user_by_prefix(u, s)
            resp_json = resp.json()
            for proxy_i in resp_json["data"]["proxy_str"]:
                ip, port, user, password = proxy_i.split(":")
                need_update.add((ip, user, password))
        for ip, user, password in need_update:
            Proxy.objects.filter(username=user, ip=ip).update(password=password, status=1)
            print(ip, user, password)


def clean_cidr():
    # 清理无效CIDR
    use_lsit = set()
    for cidr in ServerCidrThrough.objects.all():
        use_lsit.add(str(cidr.cidr_id))
    print(use_lsit)
    for cidr in Cidr.objects.all():
        if str(cidr.id) not in use_lsit:
            print(cidr.id)
            cidr.delete()


def add_cidr():
    # 清理无效CIDR
    use_lsit = []
    for acl in Acls.objects.all():
        use_lsit.append(acl)
    for cidr in Cidr.objects.all():
        for acl in use_lsit:
            CidrAclThrough.objects.create(cidr=cidr, acl=acl)


def delete_old_order():
    """
    删除expired_at 1个月前的订单
    """
    delete_list = []
    utc_now = datetime.datetime.now().astimezone(pytz.utc)
    orders = Orders.objects.filter(expired_at__lt=utc_now - datetime.timedelta(days=17)).all()
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


def fix_old_proxy_order_stock():
    """
    修复旧订单的库存
    """
    acl_group_acl_reverse = {}
    acls = list(Acls.objects.all().values_list("id", flat=True))
    for acl in AclGroup.objects.all():
        acl_group_acl_reverse[acl.id] = copy.deepcopy(acls)

    for acl in AclGroupThrough.objects.all():
        if acl.acl_id in acl_group_acl_reverse[acl.acl_group_id]:
            acl_group_acl_reverse[acl.acl_group_id].remove(acl.acl_id)
    fix_dict = {}
    for ip_stock_i in ProxyStock.objects.filter(acl_group__isnull=False).all():
        cidr_id = ip_stock_i.cidr_id
        cart_step = ip_stock_i.cart_step
        new_ip_stocks = ProxyStock.objects.filter(cidr_id=cidr_id, acl_group_id=None, cart_step=cart_step).all()
        for new_ip_stock in new_ip_stocks:
            if new_ip_stock.acl_id in acl_group_acl_reverse[ip_stock_i.acl_group_id]:
                if new_ip_stock.id not in fix_dict:
                    fix_dict[new_ip_stock.id] = []
                fix_dict[new_ip_stock.id].append(ip_stock_i.available_subnets)
    for k, v in fix_dict.items():
        if "" in v:
            v = [""]
        else:
            if len(v) > 1:
                cidr_list = []
                for x in v:
                    cidr_list.append(set(x.split(",")))
                intersection = cidr_list[0]
                for s in cidr_list[1:]:
                    intersection = intersection & s
                intersection = list(intersection)
                intersection.sort(key=lambda x: int(ipaddress.ip_network(x).network_address))
                v = [",".join(intersection)]
        stock_ = ProxyStock.objects.filter(id=k).first()
        stock_.available_subnets = v[0]
        stock_.ip_stock = len(v[0].split(",")) * stock_.cart_step if v[0] else 0
        stock_.save()
        print(k, v[0], stock_.ip_stock)


def find_proxy_stock_ids():
    acl_group_acl_reverse = {}
    acls = list(Acls.objects.all().values_list("id", flat=True))
    for acl in AclGroup.objects.all():
        acl_group_acl_reverse[acl.id] = copy.deepcopy(acls)

    for acl in AclGroupThrough.objects.all():
        if acl.acl_id in acl_group_acl_reverse[acl.acl_group_id]:
            acl_group_acl_reverse[acl.acl_group_id].remove(acl.acl_id)
    for p in Proxy.objects.all():
        try:
            ip_stock_id = p.ip_stock_id
            acl_group_id = ProxyStock.objects.filter(id=ip_stock_id).first().acl_group_id
            acl_ids = acl_group_acl_reverse.get(acl_group_id, [])
            ip_stock_ids = ProxyStock.objects.filter(acl_id__in=acl_ids, subnets__contains=p.subnet).all()
            p.ip_stock_ids = ",".join([str(x.id) for x in ip_stock_ids])
            p.save()
        except Exception as e:
            print(e)


def fix_ip_stock_item():
    acls = list(Acls.objects.all().values_list("id", flat=True))
    for ip_s in ProxyStock.objects.filter(acl_group__isnull=False).all():
        # 扩展库存
        for acl_i in acls:
            obj, is_create = ProxyStock.objects.get_or_create(cidr_id=ip_s.cidr_id, acl_id=acl_i,
                                                              cart_step=ip_s.cart_step)
            if is_create:
                obj.subnets = ip_s.subnets
                obj.available_subnets = ip_s.subnets
                obj.ip_stock = ip_s.ip_stock
                obj.save()
                print(obj.id)


def delete_product():
    p_set = set()
    for x in ProductStock.objects.all():
        key = "-".join((str(x.variant.id), str(x.acl_id)))
        if key in p_set:
            x.delete()
            print(x.id)
        else:
            p_set.add(key)



def fix_cidrs():
    for x in Variant.objects.all():
        cidrs = x.server_group.get_cidrs()
        x.cidrs.clear()
        for cidr in cidrs:
            x.cidrs.add(cidr)
            print(cidr.id, x.id)


def update_product_stock():
    """
    更新product_stock表
    """
    for x in ProductStock.objects.all():
        s=x.stock
        x.save()
        if s!=x.stock:
            print(x.id)


def fix_exclude_cidr():
    for x in Cidr.objects.all():
        exclude_acls = x.exclude_acl.all()
        ProxyStock.objects.filter(cidr_id=x.id, acl_id__in=exclude_acls).update(exclude_label=True)
    for x in ProductStock.objects.all():
        x.save()
def fix_proxy_cidr_variant():
    """
    修复proxy表中的cidr_id和variant_id
    """
    for x in Proxy.objects.all():
        cidr_p=x.subnet
        c_o=Cidr.objects.filter(cidr=cidr_p).first()
        if c_o:
            x.cidr_id=c_o.id
        else:
            ids=x.ip_stock_ids.split(",")
            x.cidr_id=ProxyStock.objects.filter(id__in=ids).first().cidr_id
        x.local_variant_id=x.order.local_variant_id
        x.save()



if __name__ == '__main__':
    add_product_other()
    # fix_stocks()
