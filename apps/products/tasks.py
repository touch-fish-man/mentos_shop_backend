from apps.products.models import Variant, ProductTag, ProductTagRelation, Product
from celery import shared_task

from apps.proxy_server.models import ProxyStock, Proxy, Acls, ServerGroupThrough, ServerCidrThrough, ProductStock


@shared_task(bind=True, name='update_product_stock')
def update_product_stock(*args, **kwargs):
    """
    更新商品库存
    """
    stock_data = {}

    stock_id = kwargs.get("ip_stock_id")
    if stock_id:
        target_stocks = list(ProxyStock.objects.filter(id=stock_id))
    else:
        target_stocks = list(ProxyStock.objects.all())

    # Get all related proxies in one query
    stock_ids = [stock.id for stock in target_stocks]
    all_related_proxies = Proxy.objects.filter(ip_stock_id__in=stock_ids)

    # Group proxies by ip_stock_id
    proxies_grouped_by_stock = {}
    for proxy in all_related_proxies:
        if proxy.ip_stock_id not in proxies_grouped_by_stock:
            proxies_grouped_by_stock[proxy.ip_stock_id] = []
        proxies_grouped_by_stock[proxy.ip_stock_id].append(proxy)

    stocks_to_update = []

    for stock in target_stocks:
        related_proxies = proxies_grouped_by_stock.get(stock.id, [])

        if stock.subnets:
            all_subnets = set(stock.subnets.split(","))
            used_subnets = set(proxy.subnet for proxy in related_proxies if proxy.subnet in all_subnets)
            available_subnets_list = sorted(list(all_subnets - used_subnets))
            available_count = len(available_subnets_list)

            if stock.cart_stock != available_count:
                stock.cart_stock = available_count
                stock.available_subnets = ",".join(available_subnets_list)
                stock.ip_stock = available_count * stock.cart_step
                stocks_to_update.append(stock.id)
                stock_data[stock.id] = stock.ip_stock
                stock.save()

    # # Bulk save updated objects
    # if stocks_to_update:
    #     ProxyStock.objects.bulk_update(stocks_to_update, ['cart_stock', 'available_subnets', 'ip_stock'])

    # If the number of Variant.objects.all() is large, consider only updating those that have indeed changed
    for variant in Variant.objects.all():
        variant.save()

    return stock_data


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


@shared_task(name='update_product_acl')
def update_product_acl(acls=None):
    if not acls:
        acls = Acls.objects.all()
    else:
        acls = Acls.objects.filter(id__in=acls)
    products = Product.objects.all()
    for product in products:
        Variants = Variant.objects.filter(product=product).all()
        # 创建variant
        for idx, v in enumerate(Variants):
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
                product_stock, is_create = ProductStock.objects.get_or_create(product=product, acl_id=acl_i.id,
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
        print("更新商品", product.id)
