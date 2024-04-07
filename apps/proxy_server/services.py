from apps.products.models import Variant
from apps.proxy_server.models import Acls, ProxyStock


def update_product_acl(acl_ids=None):
    # 创建产品变体
    if acl_ids is None:
        acl_ids= Acls.objects.filter(soft_delete=False).values_list('id', flat=True)
    for acl_id in acl_ids:
        variant = Variant.objects.all()
        for v in variant:
            new_variant,is_create = Variant.objects.get_or_create(product_id=v.product_id, option1=v.option1, option2=v.option2,
                                                        option3=v.option3, acl_id=acl_id)
            if is_create:
                for field in v._meta.fields:
                    if field.name != 'id' and field.name != 'acl_id':
                        setattr(new_variant, field.name, getattr(v, field.name))
                new_variant.save()
        for ip_s in ProxyStock.objects.filter(acl_group__isnull=False).all():
                obj, is_create = ProxyStock.objects.get_or_create(cidr_id=ip_s.cidr_id, acl_id=acl_id,
                                                                  cart_step=ip_s.cart_step)
                if is_create:
                    obj.subnets = ip_s.subnets
                    obj.available_subnets = ip_s.subnets
                    obj.ip_stock = ip_s.ip_stock
                    obj.save()
    return True