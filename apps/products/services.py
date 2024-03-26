from ipaddress import ip_network
from pprint import pprint
from collections import OrderedDict
from apps.products.models import Variant
from apps.proxy_server.models import ProductStock, Acls, ProxyStock



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
            acl_i=Acls.objects.get(id=stock.acl_id)
            acl_name = acl_i.name
            acl_price = acl_i.price
        except:
            acl_name = ''
            acl_price = 0
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
        proxy_stocks = ProxyStock.objects.filter(cidr_id=cidr_id, cart_step=cart_step, acl_id__in=acl_ids).all()
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
        acl_list = option1.split(',')
        available_cidrs_dict = get_available_cidrs(acl_list, cidr_list, cart_step)
        stock = len(available_cidrs_dict) * cart_step
        data["stock"] = stock
        data["local_variant_id"] = variant.id
        data["shopify_variant_id"] = variant.shopify_variant_id
    return data
