import logging
import time
from ipaddress import ip_network
from collections import OrderedDict

from django.core.cache import cache

from apps.products.models import Variant, Product
from apps.proxy_server.models import ProductStock, Acls, ProxyStock, ServerGroupThrough, ServerCidrThrough


def get_stock(product_id, variant_option1, variant_option2, variant_option3):
    product_stock = ProductStock.objects.filter(product_id=product_id)
    if variant_option1:
        product_stock = product_stock.filter(option1=variant_option1)
    if variant_option2:
        product_stock = product_stock.filter(option2=variant_option2)
    if variant_option3:
        product_stock = product_stock.filter(option3=variant_option3)
    product_stock = product_stock.all()
    stocks = []
    for stock in product_stock:
        try:
            acl_i_dict = Acls.get_acl_cache(stock.acl_id)
            acl_name = acl_i_dict.get('name', '')
            acl_price = acl_i_dict.get('price', 0)
        except Exception as e:
            logging.info(e)
            continue
        tmp_dict = {}
        tmp_dict['acl_id'] = stock.acl_id
        tmp_dict['acl_name'] = acl_name
        tmp_dict['option2'] = stock.option2
        tmp_dict['option3'] = stock.option3
        tmp_dict['stock'] = stock.stock
        tmp_dict['price'] = acl_price
        stocks.append(tmp_dict)
    return stocks


def sort_cidr(cidr_list):
    sorted_ip_networks = sorted(cidr_list, key=lambda net: int(ip_network(net).network_address))
    sorted_ip_networks_cidr = [str(net) for net in sorted_ip_networks]
    return sorted_ip_networks_cidr


def get_available_cidrs(acl_ids, cidr_ids, cart_step):
    """
    获取可发货的cidr，寻找在指定的acl_ids和cidr_ids中的可用子网交集，并记录它们的proxy_stock_id。
    """
    available_cidrs = {}  # 结果列表

    # 对于每个CIDR ID
    for cidr_id in cidr_ids:
        # 使用字典记录每个CIDR对应的ProxyStock ID列表
        subnet_proxy_stock_map = {}
        proxy_stocks = ProxyStock.objects.filter(cidr_id=cidr_id, cart_step=cart_step, acl_id__in=acl_ids,
                                                 soft_delete=False).all()
        for proxy_stock in proxy_stocks:
            # 解析可用子网字符串
            available_subnets = proxy_stock.available_subnets.split(',')
            acl_id = proxy_stock.acl_id
            for subnet in available_subnets:
                if subnet not in subnet_proxy_stock_map:
                    subnet_proxy_stock_map[subnet] = [set(), set()]
                subnet_proxy_stock_map[subnet][0].add(acl_id)
                subnet_proxy_stock_map[subnet][1].add((proxy_stock, acl_id))
                if len(subnet_proxy_stock_map[subnet][0]) == len(acl_ids):
                    available_cidrs[subnet] = subnet_proxy_stock_map[subnet][1]
    available_cidrs = OrderedDict(sorted(available_cidrs.items(), key=lambda x: int(ip_network(x[0]).network_address)))
    return available_cidrs


def get_variant_info(product_id, option1, option2, option3, acl_selected):
    data = {"price": 0, "stock": 0, "local_variant_id": 0, "shopify_variant_id": "0", "base_price": 0, "acl_price": 0}
    acl_selected= acl_selected.split(",")
    variant = Variant.objects.filter(product_id=product_id)
    if option1:
        variant = variant.filter(variant_option1=option1)
    if option2:
        variant = variant.filter(variant_option2=option2)
    if option3:
        variant = variant.filter(variant_option3=option3)
    variant = variant.first()
    cidr_list = []
    if variant:
        data['base_price'] = variant.variant_price
        acls = Acls.objects.filter(id__in=acl_selected).all().values_list("price", flat=True)
        if acls:
            data["acl_price"] = sum(acls)  # acl的价格
        data['price'] += float(data['base_price']) + float(data['acl_price'])
        cart_step = variant.cart_step
        for cidr in variant.cidrs.all():
            cidr_list.append(cidr.id)
        available_cidrs_dict = get_available_cidrs(acl_selected, cidr_list, cart_step)
        stock = len(available_cidrs_dict) * cart_step
        data["stock"] = stock
        data["local_variant_id"] = variant.id
        data["shopify_variant_id"] = variant.shopify_variant_id
    return data


def get_cidr(server_group):
    cidrs = []
    if server_group:
        server_ids = ServerGroupThrough.objects.filter(server_group_id=server_group.id).values_list('server_id',
                                                                                                    flat=True)
        for x in ServerCidrThrough.objects.filter(server_id__in=server_ids).all():
            cidrs.append(x.cidr)
        return cidrs
    else:
        return cidrs


def add_product_other():
    acls = Acls.objects.all()
    Variants = Variant.objects.all()
    # 创建variant
    for idx, v in enumerate(Variants):
        product =v.product
        cart_step = v.cart_step
        server_group = v.server_group
        cidrs = get_cidr(server_group)
        for acl_i in acls:
            ip_stock_objs = []
            for cidr_i in cidrs:
                v.cidrs.add(cidr_i)
                cart_stock = cidr_i.ip_count // cart_step
                stock_obj, is_create = ProxyStock.objects.get_or_create(cidr=cidr_i, acl=acl_i, cart_step=cart_step)
                if is_create:
                    stock_obj.ip_stock = cidr_i.ip_count
                    stock_obj.cart_stock = cart_stock
                    subnets = stock_obj.gen_subnets()
                    stock_obj.subnets = ",".join(subnets)
                    stock_obj.available_subnets = stock_obj.subnets
                    stock_obj.save()
                stock_obj.soft_delete = False
                stock_obj.save()
                ip_stock_objs.append(stock_obj)
            product_stock, is_create= ProductStock.objects.get_or_create(product=product, acl_id=acl_i.id,
                                                        option1=v.variant_option1,
                                                        option2=v.variant_option2,
                                                        option3=v.variant_option3,
                                                        cart_step=cart_step, old_variant_id=v.id,
                                                        server_group=server_group)
            stock = 0
            for ip_stock_obj in ip_stock_objs:
                product_stock.ip_stocks.add(ip_stock_obj)
                stock += ip_stock_obj.ip_stock
            product_stock.stock = stock
            product_stock.save()
        # print("更新商品", v.id)
