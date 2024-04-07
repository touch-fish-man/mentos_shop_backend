from apps.proxy_server.models import Acls, ProxyStock

def update_product_acl(acl_ids=None):
    # 创建产品变体
    if acl_ids is None:
        acl_ids= Acls.objects.filter(soft_delete=False).values_list('id', flat=True)
    for acl_id in acl_ids:
        for ip_s in ProxyStock.objects.filter(acl_group__isnull=False).all():
                obj, is_create = ProxyStock.objects.get_or_create(cidr_id=ip_s.cidr_id, acl_id=acl_id,
                                                                  cart_step=ip_s.cart_step)
                if is_create:
                    obj.subnets = ip_s.subnets
                    obj.available_subnets = ip_s.subnets
                    obj.ip_stock = ip_s.ip_stock
                    obj.save()
                    print("创建", obj.id)
    return True