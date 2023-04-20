import datetime
import hmac
import hashlib
import base64
from datetime import timezone
import re

from apps.utils.shopify_handler import ShopifyClient
from django.conf import settings
from apps.rewards.models import LevelCode
from .models import Orders
from apps.proxy_server.models import Server, Proxy, ServerGroup, ProxyStock
from apps.products.models import Product, Variant
from apps.utils.kaxy_handler import KaxyClient
from apps.users.models import User


def verify_webhook(request):
    shopify_hmac_header = request.META.get("HTTP_X_SHOPIFY_HMAC_SHA256")
    encoded_secret = settings.SHOPIFY_WEBHOOK_KEY.encode("utf-8")
    digest = hmac.new(
        encoded_secret,
        request.body,
        digestmod=hashlib.sha256,
    ).digest()
    computed_hmac = base64.b64encode(digest)
    return hmac.compare_digest(computed_hmac, shopify_hmac_header.encode("utf-8"))


def shopify_order(data):
    """
    Format the order data to be sent to the client
    """
    discount_codes = []
    for discount in data["discount_codes"]:
        discount_codes.append(discount["code"])
    return_data = {
        "order_id": str(data["id"]),
        "order": {
            "created_at": data["created_at"],
            "total_price": data["total_price"], # 总价
            "total_weight": data["total_weight"],
            "currency": data["currency"],
            "financial_status": data["financial_status"], # 支付状态
            "order_number": data["order_number"], # 订单号
            "order_status_url": data["order_status_url"],
            "line_items": data["line_items"],
        },
        "note": data["note"],
        discount_codes: discount_codes,
        "note_attributes": data["note_attributes"],

    }
    for note in data["note_attributes"]:
        return_data[note.get('name')] = note.get('value')

    return return_data


def get_checkout_link(request):
    user = request.user
    user_level = user.level
    level_code_obj = LevelCode.objects.filter(level=user_level).first()
    # 创建订单
    order_info_dict = {}
    order_info_dict["uid"] = user.id
    order_info_dict["username"] = user.username
    order_info_dict["product_id"] = request.data.get("product_id")
    order_info_dict["product_quantity"] = request.data.get("quantity")
    option_selected=request.data.get("option_selected")
    variant_obj = Variant.objects.filter(product=order_info_dict["product_id"], variant_option1=option_selected[0])
    if len(option_selected) == 2:
        variant_obj = variant_obj.filter(variant_option2=option_selected[1])
    # 查询产品信息
    variant_obj = variant_obj.first()
    if variant_obj:
        order_info_dict["variant_id"] = variant_obj.shopify_variant_id
        order_info_dict["product_price"] = variant_obj.variant_price
        order_info_dict["local_variant_id"] = variant_obj.id
        proxy_time = variant_obj.proxy_time
        order_info_dict["product_total_price"] = order_info_dict["product_price"] * int(order_info_dict["product_price"])
        order_info_dict["product_type"] = Product.objects.filter(id=order_info_dict["product_id"]).first().product_collections.first().id
        expired_at = datetime.datetime.now(timezone.utc)+datetime.timedelta(days=proxy_time)
        order_info_dict["expired_at"] = expired_at
        order_info_dict["proxy_time"]=proxy_time
        new_order = Orders.objects.create(**order_info_dict)
        order_id=new_order.order_id
        if level_code_obj:
            code = level_code_obj.code
        else:
            code = None
        cart_quantity_pairs = ["{}:{}".format(order_info_dict["variant_id"], order_info_dict["product_quantity"])]
        check_info = {
            "cart_quantity_pairs": cart_quantity_pairs,
            "discount": code,
            "email": user.email,
            "note": "order_id_{}".format(order_id),
            'attributes': {"order_id": order_id, "renewal": request.data.get("renewal", "0")},
            "ref": "mentosproxy_web",
        }
        checkout_link = ShopifyClient.get_checkout_link(settings.SHOPIFY_SHOP_URL, check_info)
        new_order.checkout_link = checkout_link
        new_order.save()
        return checkout_link, order_id
    else:
        return None, None

def get_renew_checkout_link(order_id):
    order_obj = Orders.objects.filter(order_id=order_id).first()
    if order_obj:
        checkout_link=order_obj.checkout_link
        renew_checkot_url=re.sub(r'attributes\[renewal\]=\d', 'attributes[renewal]=1', checkout_link)
        return renew_checkot_url,order_id
    else:
        return None, None

def create_proxy_by_order(order_id):
    """
    根据订单创建代理
    """
    order_obj = Orders.objects.filter(order_id=order_id,pay_status=1).first()
    if order_obj:
        order_user_obj = User.objects.filter(id=order_obj.uid).first()
        order_user = order_obj.username
        order_id = order_obj.order_id
        proxy_username = order_user + order_id[:6]  # 生成代理用户名
        variant_obj = Variant.objects.filter(id=order_obj.local_variant_id).first()  # 获取订单对应的套餐
        if variant_obj:
            if variant_obj.variant_stock < order_obj.product_quantity:
                # 库存不足
                print('库存不足')
                return False
            server_group = variant_obj.server_group
            acl_group = variant_obj.acl_group
            cart_step = variant_obj.cart_step  # 购物车步长
            acl_value = acl_group.acl_value  # 获取acl组的acl值
            server_group_obj = ServerGroup.objects.filter(id=server_group.id).first()
            proxy_expired_at = order_obj.expired_at  # 代理过期时间
            proxy_list = []
            server_list = []
            if server_group_obj:
                servers = server_group_obj.servers.all()
                for server in servers:
                    cidr_info = server.get_cidr_info()
                    for cidr in cidr_info:
                        Stock = ProxyStock.objects.filter(acl_group=acl_group.id, cidr=cidr['id'],
                                                        variant_id=variant_obj.id).first()
                        if Stock:
                            while Stock.cart_stock > 0:
                                if len(proxy_list) >= order_obj.product_quantity:
                                    # 代理数量已经够了
                                    break
                                for i in range(order_obj.product_quantity // cart_step):
                                    kaxy_client = KaxyClient(server.ip)
                                    prefix = Stock.current_subnet
                                    proxy_info = kaxy_client.create_user_acl_by_prefix(proxy_username, prefix,acl_value)
                                    if proxy_info["proxy"]:
                                        proxy_list.extend(proxy_info["proxy"])
                                        server_list.extend([server.ip] * len(proxy_info["proxy"]))
                                        Stock.current_subnet = Stock.get_next_subnet()
                                        Stock.cart_stock -= 1
                                        Stock.ip_stock -= len(proxy_info["proxy"])
                                    Stock.save()
                        if len(proxy_list) >= order_obj.product_quantity:
                            # 代理数量已经够了
                            break
            if proxy_list:
                for idx, proxy in enumerate(proxy_list):
                    ip, port, user, password = proxy.split(":")
                    server_ip = server_list[idx]
                    Proxy.objects.create(ip=ip, port=port, username=user, password=password, server_ip=server_ip,
                                        order=order_obj, expired_at=proxy_expired_at, user=order_user_obj)
                # 更新订单状态
                order_obj.order_status = 4
                order_obj.save()
                # 更新套餐库存
                variant_obj.variant_stock -= order_obj.product_quantity
                variant_obj.save()      
                return True
    return False
def renew_proxy_by_order(order_id):
    """
    根据订单续费代理
    """
    order_obj = Orders.objects.filter(order_id=order_id,renew_status=1).first()
    if order_obj:
        proxies=Proxy.objects.filter(order=order_obj).all()
        for proxy in proxies:
            proxy.expired_at+=datetime.timedelta(days=order_obj.proxy_time)
            proxy.save()
        order_obj.expired_at+=datetime.timedelta(days=order_obj.proxy_time)
        order_obj.renew_status=0
        order_obj.save()
        return True
    return False

def change_order_proxy(order_id):
    """
    修改订单代理
    """
    # 删除订单原有代理
    order_obj = Orders.objects.filter(id=order_id).first()
    if order_obj:
        Proxy.objects.filter(order=order_obj).delete()
        # 创建新的代理
        create_proxy_by_order(order_id)