from ipaddress import ip_network
from pprint import pprint
from collections import OrderedDict
from apps.products.models import Variant, ExtendedVariant
from apps.proxy_server.models import ProductStock, Acls, ProxyStock


def get_price(product_id, option1, option2, option3):
    acl_count = len(option1.split(',')) if option1 else 0
    product = ExtendedVariant.objects.filter(product_id=product_id, variant_option1=acl_count, variant_option2=option2,
                                             variant_option3=option3).first()
    if not product:
        return 0
    return product.variant_price


def get_stock(product_id, option2, option3):
    product_stock = ProductStock.objects.filter(product_id=product_id, option2=option2,
                                                option3=option3).all()
    stocks = []
    for stock in product_stock:
        try:
            acl_name = Acls.objects.get(id=stock.acl_id).name
        except:
            acl_name = ''
        tmp_dict = {}
        tmp_dict['acl_id'] = stock.acl_id
        tmp_dict['acl_name'] = acl_name
        tmp_dict['option2'] = stock.option2
        tmp_dict['option3'] = stock.option3
        tmp_dict['stock'] = stock.stock
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


def get_variant_info(product_id, option1, option2, option3):
    data = {"price": 0, "stock": 0, "local_variant_id": 0, "shopify_variant_id": "0"}
    acl_count = len(option1.split(',')) if option1 else 0
    variant = ExtendedVariant.objects.filter(product_id=product_id, variant_option1=acl_count, variant_option2=option2,
                                             variant_option3=option3).first()
    cidr_list = []
    if variant:
        data['price'] = variant.variant_price
        old_variant = variant.old_variant
        # get cidr list from VariantCidrThroug
        for cidr in old_variant.cidrs.all():
            cidr_list.append(cidr.id)
        cart_step = old_variant.cart_step

        acl_list = option1.split(',')
        available_cidrs_dict = get_available_cidrs(acl_list, cidr_list, cart_step)

        stock = len(available_cidrs_dict) * cart_step
        data["stock"] = stock
        data["local_variant_id"] = variant.id
        data["shopify_variant_id"] = variant.shopify_variant_id
    return data
