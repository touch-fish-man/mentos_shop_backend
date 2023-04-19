import os
import sys

import django

from apps.utils.kaxy_handler import KaxyClient

if os.environ.get('DJANGO_ENV'):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if os.path.exists(os.path.join(base_dir, 'config', 'django', os.environ.get('DJANGO_ENV') + '.py')):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django." + os.environ.get('DJANGO_ENV'))
    else:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.local")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.local")
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()
from apps.orders.models import Orders
from apps.proxy_server.models import ProxyStock, ServerGroup, Proxy
from apps.products.models import Variant


def create_proxy_by_order(order_id):
    """
    根据订单创建代理
    """
    order_obj = Orders.objects.filter(id=order_id,pay_status=1).first()
    if order_obj:
        print(order_obj.variant_id)
        order_user = order_obj.username
        order_id = order_obj.order_id
        proxy_username = order_user + order_id[:6]  # 生成代理用户名
        variant_obj = Variant.objects.filter(id=order_obj.variant_id).first()  # 获取订单对应的套餐
        if variant_obj:
            if variant_obj.variant_stock < order_obj.product_quantity:
                # 库存不足
                print('库存不足')
                return False
            server_group = variant_obj.server_group
            acl_group = variant_obj.acl_group
            cart_step = variant_obj.cart_step  # 购物车步长
            acl_value = acl_group.acl_value  # 获取acl组的acl值
            server_group_obj = ServerGroup.objects.filter(id=server_group.id).first()
            proxy_expired_at = order_obj.expired_at  # 代理过期时间
            proxy_list = []
            server_list = []
            if server_group_obj:
                print('server_group_obj', server_group_obj)
                servers = server_group_obj.servers.all()
                for server in servers:
                    cidr_info = server.get_cidr_info()
                    for cidr in cidr_info:
                        Stock = ProxyStock.objects.filter(acl_group=acl_group.id, cidr=cidr['id'],
                                                        variant_id=variant_obj.id).first()
                        if Stock:
                            while Stock.cart_stock > 0:
                                if len(proxy_list) >= order_obj.product_quantity:
                                    # 代理数量已经够了
                                    break
                                for i in range(order_obj.product_quantity // cart_step):
                                    server_api_url = "http://{}:65533".format(server.ip)
                                    kaxy_client = KaxyClient(server_api_url)
                                    prefix = Stock.current_subnet
                                    print(prefix, proxy_username, server_api_url, acl_value)
                                    proxy_info = kaxy_client.create_user_acl_by_prefix(proxy_username, prefix,acl_value)
                                    if proxy_info["proxy"]:
                                        proxy_list.extend(proxy_info["proxy"])
                                        server_list.append([server.ip] * len(proxy_info["proxy"]))
                                        Stock.current_subnet = Stock.get_next_subnet()
                                        Stock.cart_stock -= 1
                                    Stock.save()
                        if len(proxy_list) >= order_obj.product_quantity:
                            # 代理数量已经够了
                            break
            if proxy_list:
                for idx, proxy in enumerate(proxy_list):
                    ip, port, user, password = proxy.split(":")
                    server_ip = server_list[idx]
                    Proxy.objects.create(ip=ip, port=port, username=user, password=password, server_ip=server_ip,
                                        order=order_obj, expired_at=proxy_expired_at, user=order_user)
                # 更新订单状态
                order_obj.order_status = 4
                order_obj.save()
                return True
    return False

if __name__ == '__main__':
    print(create_proxy_by_order(1))