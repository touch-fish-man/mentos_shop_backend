import datetime
import hmac
import hashlib
import base64
from datetime import timezone

from apps.utils.shopify_handler import ShopifyClient
from django.conf import settings
from apps.rewards.models import LevelCode
from .models import Orders
from apps.proxy_server.models import Server, Proxy, ServerGroup, ProxyStock
from apps.products.models import Product, Variant
from ..utils.kaxy_handler import KaxyClient


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
    return_data = {
        "order_id": str(data["id"]),
        "order": {
            "created_at": data["created_at"],
            "total_price": data["total_price"],
            "total_weight": data["total_weight"],
            "currency": data["currency"],
            "financial_status": data["financial_status"],
            "order_number": data["order_number"],
            "order_status_url": data["order_status_url"],
            "line_items": data["line_items"],
            "discount_codes": data["discount_codes"],
        },
        "note": data["note"],
        "note_attributes": data["note_attributes"],

    }

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
    order_info_dict["product_price"] = request.data.get("product_price")
    order_info_dict["product_quantity"] = request.data.get("product_quantity")
    order_info_dict["product_total_price"] = float(request.data.get("product_price")) * int(
        request.data.get("product_quantity"))
    order_info_dict["variant_id"] = request.data.get("variant_id")
    order_info_dict["product_type"] = request.data.get("product_type")
    expired_at = Variant.objects.filter(id=request.data.get("variant_id")).first().proxy_time + datetime.datetime.now(
        timezone.utc)
    order_info_dict["expired_at"] = expired_at
    order_id = Orders.objects.create(**order_info_dict).order_id
    if level_code_obj:
        code = level_code_obj.code
    else:
        code = None
    cart_quantity_pairs = ["{}:{}".format(request.data.get("variant_id"), request.data.get("product_quantity"))]
    check_info = {
        "cart_quantity_pairs": cart_quantity_pairs,
        "discount": code,
        "email": user.email,
        "note": "order_id_{}".format(order_id),
        'attributes': {"order_id": order_id, "renewal": request.data.get("renewal", "0")},
        "ref": "mentosproxy_web",
    }
    checkout_link = ShopifyClient.get_checkout_link(settings.SHOPIFY_SHOP_URL, check_info)
    return checkout_link, order_id


def create_proxy_by_order(order_id):
    """
    根据订单创建代理
    """
    order_obj = Orders.objects.filter(id=order_id).first()
    if order_obj:
        if order_obj.pay_status == 1:  # 支付成功
            order_user = order_obj.username
            order_id = order_obj.order_id
            proxy_username = order_user + "_" + order_id[:6]  # 生成代理用户名
            variant_obj = Variant.objects.filter(id=order_obj.variant_id).first()  # 获取订单对应的套餐
            if variant_obj:
                if variant_obj.variant_stock < order_obj.product_quantity:
                    # 库存不足
                    return False
                server_group = variant_obj.server_group
                acl_group = variant_obj.acl_group
                cart_step = order_obj.cart_step  # 购物车步长
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
                                        server_api_url = "http://{}:65533".format(server.ip)
                                        kaxy_client = KaxyClient(server_api_url)
                                        prefix = Stock.current_subnet
                                        proxy_info = kaxy_client.create_user_acl_by_prefix(proxy_username, prefix,
                                                                                           acl_value)
                                        if proxy_info["proxy"]:
                                            proxy_list.extend(proxy_info["proxy"])
                                            server_list.append([server.ip] * len(proxy_info["proxy"]))
                                            Stock.current_subnet = Stock.get_next_subnet()
                                            Stock.cart_stock -= 1
                                        Stock.save()
                            if len(proxy_list) >= order_obj.product_quantity:
                                # 代理数量已经够了
                                break
                if proxy_list:
                    for idx, proxy in enumerate(proxy_list):
                        ip, port, user, password = proxy.split(":")
                        server_ip = server_list[idx]
                        Proxy.objects.create(ip=ip, port=port, username=user, password=password, server_ip=server_ip,
                                             order=order_obj, expired_at=proxy_expired_at, user=order_user)
                    # 更新订单状态
                    order_obj.order_status = 4
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
