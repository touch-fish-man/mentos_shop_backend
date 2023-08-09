from apps.products.models import Variant, ProductTag, ProductTagRelation
from celery import shared_task

from apps.proxy_server.models import ProxyStock, Proxy


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
                stocks_to_update.append(stock)
                stock_data[stock.id] = stock.ip_stock

    # Bulk save updated objects
    if stocks_to_update:
        ProxyStock.objects.bulk_update(stocks_to_update, ['cart_stock', 'available_subnets', 'ip_stock'])

    # If the number of Variant.objects.all() is large, consider only updating those that have indeed changed
    for variant in Variant.objects.all():
        variant.save()

    return stock_data


def update_product_from_shopify():
    """
    定时任务，更新商品信息
    """
    pass
