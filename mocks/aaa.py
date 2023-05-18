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

from apps.proxy_server.models import Proxy,ProxyStock,ServerGroup,Server,AclGroup
from apps.orders.models import Orders
from apps.products.models import Variant
import ipaddress

for xxx in ProxyStock.objects.all():
    if xxx.subnets and xxx.current_subnet:
        xxx.available_subnets=xxx.subnets[xxx.subnets.index(xxx.current_subnet):]
        xxx.save()
# for ppp in Proxy.objects.all():
#     order_id=ppp.order_id
#     print(order_id)
#     order_obj = Orders.objects.filter(id=order_id).first()
#     if order_obj:
#         order_id = order_obj.order_id
#         variant_obj = Variant.objects.filter(id=order_obj.local_variant_id).first()  # 获取订单对应的套餐
#         if variant_obj:
#             server_group = variant_obj.server_group
#             acl_group = variant_obj.acl_group
#             cart_step = variant_obj.cart_step  # 购物车步长
#             acl_value = acl_group.acl_value  # 获取acl组的acl值
#             server_group_obj = ServerGroup.objects.filter(id=server_group.id).first()
#             proxy_expired_at = order_obj.expired_at  # 代理过期时间
#             proxy_list = []
#             server_list = []
#             stock_list = []
#             subnet_list = []
#             if server_group_obj:
#                 servers = server_group_obj.servers.all()
#                 for server in servers:
#                     cidr_info = server.get_cidr_info()
#                     for cidr in cidr_info:
#                         Stock = ProxyStock.objects.filter(acl_group=acl_group.id, cidr=cidr['id'],
#                                                         variant_id=variant_obj.id).first()
#                         for c in Stock.subnets.split(","):
#                             if ipaddress.IPv4Address(ppp.ip) in ipaddress.IPv4Network(c):
#                                 ppp.subnet=c
#                                 ppp.ip_stock_id=Stock.id
#                                 ppp.save()
