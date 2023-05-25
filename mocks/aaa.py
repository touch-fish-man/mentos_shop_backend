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

from apps.proxy_server.models import Proxy,ProxyStock,ServerGroup,Server,AclGroup
from apps.orders.models import Orders
from apps.products.models import Variant
import ipaddress

# for xxx in ProxyStock.objects.all():
#     ppp=Proxy.objects.filter(ip_stock_id=xxx.id).all()
#     if xxx.subnets:
#         subnets=xxx.subnets.split(",")
#         for p in ppp:
#             if p.subnet in subnets:
#                 subnets.remove(p.subnet)
#         subnets.sort()
#         cart_stock=len(subnets)
#         xxx.available_subnets=",".join(subnets)
#         # print(xxx.available_subnets)
#         if xxx.cart_stock!=cart_stock:
#             print(xxx.cart_stock,cart_stock,xxx.id)
#             print(xxx.cart_stock*xxx.cart_step,cart_stock*xxx.cart_step)
#             xxx.cart_stock=cart_stock
#             xxx.available_subnets=",".join(subnets)
#             xxx.ip_stock=cart_stock*xxx.cart_step
#             xxx.save()
v_idlist= Variant.objects.values_list("id",flat=True).all()
s_list= ProxyStock.objects.values_list("variant_id",flat=True).all()
for v_id in v_idlist:
    if v_id not in s_list:
        V=Variant.objects.filter(id=v_id).first()
        print(V.id,V.acl_group_id)

print("--------------")
for s_id in s_list:
    if s_id not in v_idlist:
        print(s_id)
        s=ProxyStock.objects.filter(variant_id=s_id).first()
        print(s.id,s.acl_group_id)



# for x in Variant.objects.all():
#     x.save()
# for ddd in Orders.objects.all():
#
#     if ddd.expired_at.replace(tzinfo=None)<=datetime.datetime.utcnow():
#         ddd.status=3
#         ddd.delete()


