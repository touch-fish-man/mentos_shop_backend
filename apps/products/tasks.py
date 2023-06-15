from apps.products.models import Variant, ProductTag, ProductTagRelation
from celery import shared_task

from apps.proxy_server.models import ProxyStock, Proxy


@shared_task(bind=True, name='update_product_stock')
def update_product_stock(*args, **kwargs):
    """
    更新商品库存
    """
    data={}
    if kwargs.get("ip_stock_id"):
        stocks=ProxyStock.objects.filter(id=kwargs.get("ip_stock_id")).all()
    else:
        stocks=ProxyStock.objects.all()
    for xxx in stocks:
        ppp = Proxy.objects.filter(ip_stock_id=xxx.id).all()
        if xxx.subnets:
            subnets = xxx.subnets.split(",")
            for p in ppp:
                if p.subnet in subnets:
                    subnets.remove(p.subnet)
            subnets.sort()
            cart_stock = len(subnets)
            xxx.available_subnets = ",".join(subnets)
            if xxx.cart_stock != cart_stock:
                xxx.cart_stock = cart_stock
                xxx.available_subnets = ",".join(subnets)
                xxx.ip_stock = cart_stock * xxx.cart_step
                xxx.save()
                data[xxx.id] = xxx.ip_stock
    for x in Variant.objects.all():
        x.save()
    return data


def update_product_from_shopify():
    """
    定时任务，更新商品信息
    """
    pass
