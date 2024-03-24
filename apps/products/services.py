from apps.products.models import Variant,ExtendedVariant
from apps.proxy_server.models import ProductStock,Acls


def get_price(product_id, option1, option2, option3):
    acl_count = len(option1.split(',')) if option1 else 0
    product = ExtendedVariant.objects.filter(product_id=product_id, variant_option1=acl_count, variant_option2=option2, variant_option3=option3).first()
    if not product:
        return 0
    return product.variant_price


def get_stock(product_id,option2, option3):
    product_stock = ProductStock.objects.filter(product_id=product_id, option2=option2,
                                                option3=option3).all()
    stocks = []
    for stock in product_stock:
        try:
            acl_name= Acls.objects.get(id=stock.acl_id).name
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


def get_variant_info(product_id, option1, option2, option3):
    data = {}
    acl_count = len(option1.split(',')) if option1 else 0
    variant = ExtendedVariant.objects.filter(product_id=product_id, variant_option1=acl_count, variant_option2=option2, variant_option3=option3).first()
    if variant:
        price=variant.variant_price
    else:
        price = 0
    acl_list=option1.split(',')
    stock = 1024
    data['price'] = price
    data['stock'] = stock
    data["local_variant_id"] = variant.id
    data["shopify_variant_id"] = variant.shopify_variant_id
    return data
