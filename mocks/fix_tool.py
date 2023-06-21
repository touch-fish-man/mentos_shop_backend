import datetime
import random
import string

from faker import Faker
import os
import sys
import requests
import time
from concurrent.futures import ThreadPoolExecutor

from init_env import *
from rich.console import Console
import ipaddress
from apps.core.cache_lock import memcache_lock
console = Console()
from apps.proxy_server.tasks import create_proxy_task
from apps.proxy_server.models import Proxy, ProxyStock, ServerGroup, Server, AclGroup, ServerCidrThrough, \
    ServerGroupThrough, Cidr
from apps.orders.models import Orders
from apps.products.models import Variant, ProductTag, ProductTagRelation
from apps.utils.kaxy_handler import KaxyClient

def is_ip_in_network(ip_str, network_str):
    ip = ipaddress.ip_address(ip_str)
    network = ipaddress.ip_network(network_str)
    return ip in network
# 库存修复
def fix_stock():
    for xxx in ProxyStock.objects.all():
        ppp=Proxy.objects.filter(ip_stock_id=xxx.id).all()
        if xxx.subnets:
            subnets=xxx.subnets.split(",")
            for p in ppp:
                if p.subnet in subnets:
                    subnets.remove(p.subnet)
            subnets.sort()
            cart_stock=len(subnets)
            xxx.available_subnets=",".join(subnets)
            # print(xxx.available_subnets)
            if xxx.cart_stock!=cart_stock:
                print(xxx.cart_stock,cart_stock,xxx.id)
                xxx.cart_stock=cart_stock
                xxx.available_subnets=",".join(subnets)
                xxx.ip_stock=cart_stock*xxx.cart_step
                xxx.save()
    for x in Variant.objects.all():
        x.save()
# 删除多余库存数据
def delete_stock():
    for xxx in ProxyStock.objects.all():
        ppp=Proxy.objects.filter(ip_stock_id=xxx.id).all() # 没有发货数据
        va=Variant.objects.filter(id=xxx.variant_id).first() # 没有商品数据
        if not ppp and not va:
            print(xxx.id)
            xxx.delete()
# delete_stock()
def get_cidr(server_group):
    cidr_ids = []
    if server_group:

        server_ids=ServerGroupThrough.objects.filter(server_group_id=server_group.id).values_list('server_id', flat=True)
        cidr_ids=ServerCidrThrough.objects.filter(server_id__in=server_ids).values_list('cidr_id', flat=True)
        ip_count = Cidr.objects.filter(id__in=cidr_ids).values_list('ip_count', flat=True)
        return cidr_ids,ip_count
    else:
        return cidr_ids,[]
def fix_cidr():
    # 查询所有产品
    for variant_obj in Variant.objects.all():
        servers = variant_obj.server_group.servers.all()
        acl_group = variant_obj.acl_group.id

        for server in servers:
            cidr_info = server.get_cidr_info()
            for cidr_i in cidr_info:
                ip_stock = cidr_i.get('ip_count')
                if not ProxyStock.objects.filter(variant_id=variant_obj.id, acl_group_id=acl_group, cidr_id=cidr_i['id']).exists():
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
    tag_dict={}
    for product_tag in ProductTag.objects.all():
        if product_tag.tag_name not in tag_dict:
            tag_dict[product_tag.tag_name]=[]
            tag_dict[product_tag.tag_name].append(product_tag.id)
        else:
            tag_dict[product_tag.tag_name].append(product_tag.id)
            tag_dict[product_tag.tag_name].sort()
    for relation in ProductTagRelation.objects.all():
        # 合并商品标签关系
        for tag_k,tag_v in tag_dict.items():
            if relation.product_tag_id in tag_v[1:]:
                relation.product_tag_id=tag_v[0]
                relation.save()
                print("合并商品标签关系",relation.id)
    # 删除多余商品标签
    for tag_k,tag_v in tag_dict.items():
        for tag_id in tag_v[1:]:
            ProductTag.objects.filter(id=tag_id).delete()
            print("删除多余商品标签",tag_id)
# fix_product()
def classify_stock():
    proxy_stock_dict={}
    for sss in ProxyStock.objects.all():
        # 根据cidr_id,acl_group_id,car_step合并库存
        key="-".join((str(sss.cidr_id),str(sss.acl_group_id),str(sss.cart_step)))
        if key not in proxy_stock_dict:
            proxy_stock_dict[key]=[]
            proxy_stock_dict[key].append(sss.id)
        else:
            proxy_stock_dict[key].append(sss.id)
            proxy_stock_dict[key].sort()
    for k,v in proxy_stock_dict.items():
        for id in v[1:]:
            # 修改proxy表中的库存id
            Proxy.objects.filter(ip_stock_id=id).update(ip_stock_id=v[0])
            # 删除多余库存
            ProxyStock.objects.filter(id=id).delete()
            print("删除多余库存",id)
def find_repeat():
    # 查找重复发货代理
    cnt=0
    xxx={}
    order_id=set()
    order_=set()
    for ppp in Proxy.objects.all():
        key="-".join((str(ppp.ip),str(ppp.ip_stock_id)))
        if key in xxx:
            print(ppp.id,ppp.subnet,ppp.ip_stock_id,ppp.order_id,xxx[key])
            order_.add((ppp.order_id,xxx[key]))
            order_id.add(ppp.order_id)
            cnt+=1
        else:
            xxx[key]=ppp.order_id
    print(cnt)
    order_=list(order_)
    #根据第二个元素排序
    order_.sort(key=lambda x:x[1])
    for xi in order_:
        print(xi)
# find_repeat()
def proxy_compare_order():
    # 比较发货代理和订单
    cnt=0
    xxx={}
    order_id=set()
    order_=set()
    for ppp in Proxy.objects.all():
        if ppp.order_id in xxx:
            xxx[ppp.order_id]+=1
        else:
            xxx[ppp.order_id]=1
        if not ppp.subnet:
            for s in ProxyStock.objects.filter(id=ppp.ip_stock_id).first().gen_subnets():
                if is_ip_in_network(ppp.ip,s):
                    ppp.subnet=s
                    ppp.save()
                    break
    # for ooo in Orders.objects.all():
    #     if ooo.id in xxx:
    #         if xxx[ooo.id]!=ooo.proxy_num:
    #             ppp=Proxy.objects.filter(order_id=ooo.id).first()
    #             username=ppp.username
    #             server_ip=ppp.server_ip
                    

                 
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
    proxies=[]
    for i in Proxy.objects.all():
        # 检测代理是否可用
        proxy_str=f"{i.username}:{i.password}@{i.ip}:{i.port}"
        proxies.append(proxy_str)
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(check_proxy, proxies)
    invalid_proxy=[proxy for proxy, result in zip(proxies, results) if result]
    with open("invalid_proxy.txt","w") as f:
        f.write("\n".join(invalid_proxy))

if __name__ == '__main__':
    # fix_product()
    # classify_stock()
    kc=KaxyClient("112.75.252.6")
    user_dict={}
    for x in Proxy.objects.filter(server_ip="112.75.252.6",status=0).all():
        if x.username not in user_dict:
            user_dict[x.username]=set()
        user_dict[x.username].add(x.subnet)
    for u,sub_ in user_dict.items():
        for s in sub_:
            resp=kc.create_user_by_prefix(u,s)
            resp_json = resp.json()
            for proxy_i in resp_json["data"]["proxy_str"]:
                ip, port, user, password = proxy_i.split(":")
                # 更新代理密码
                Proxy.objects.filter(username=u,ip=ip).update(password=password,status=1)
                print("更新代理密码",u,ip,password)