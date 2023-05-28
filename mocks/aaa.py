import datetime
import random
import string

from faker import Faker
import os
import sys
import time
from init_env import *
from rich.console import Console
import ipaddress

console = Console()

from apps.proxy_server.models import Proxy, ProxyStock, ServerGroup, Server, AclGroup, ServerCidrThrough, \
    ServerGroupThrough, Cidr
from apps.orders.models import Orders
from apps.products.models import Variant, ProductTag, ProductTagRelation
import ipaddress
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
                print(xxx.cart_stock*xxx.cart_step,cart_stock*xxx.cart_step)
                xxx.cart_stock=cart_stock
                xxx.available_subnets=",".join(subnets)
                xxx.ip_stock=cart_stock*xxx.cart_step
                xxx.save()
    for x in Variant.objects.all():
        x.save()
# fix_stock()
# 删除多余库存数据
def delete_stock():
    for xxx in ProxyStock.objects.all():
        ppp=Proxy.objects.filter(ip_stock_id=xxx.id).all() # 没有发货数据
        va=Variant.objects.filter(id=xxx.variant_id).first() # 没有商品数据
        if not ppp and not va:
            print(xxx.id)
            xxx.delete()
delete_stock()
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