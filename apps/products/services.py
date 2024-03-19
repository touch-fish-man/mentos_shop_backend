from apps.products.models import Variant
from apps.proxy_server.models import ProductStock


def get_price(product_id, option1, option2, option3):
    acl_count = len(option1.split(',')) if option1 else 0
    product = Variant.objects.filter(product_id=product_id, option1=acl_count, option2=option2, option3=option3).first()
    if not product:
        return 0
    return product.price


def get_stock(product_id, option1, option2, option3):
    product_stock = ProductStock.objects.filter(product_id=product_id, option1=option1, option2=option2,
                                                option3=option3).first()
    if not product_stock:
        return 0
    return product_stock.stock


def get_variant_info(product_id, option1, option2, option3):
    data = {}
    acl_count = len(option1.split(',')) if option1 else 0
    variant = Variant.objects.filter(product_id=product_id, option1=acl_count, option2=option2, option3=option3).first()
    if not variant:
        return data
    stock = get_stock(product_id, option1, option2, option3)
    data['price'] = variant.price
    data['stock'] = stock
    data["local_variant_id"] = variant.id
    data["shopify_variant_id"] = variant.shopify_variant_id
    return data
