from apps.products.models import Variant, ProductTag, ProductTagRelation
from celery import shared_task


@shared_task(bind=True, name='update_product_stock')
def update_product_stock():
    """
    更新商品库存
    """
    for v in Variant.objects.all():
        v.update_stock()
        print("更新库存", v.id)


def update_product_from_shopify():
    """
    定时任务，更新商品信息
    """
    pass
