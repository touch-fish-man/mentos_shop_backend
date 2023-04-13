import hmac
import hashlib
import base64
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
    order_obj = Orders.objects.filter(id=order_id).first()
    if order_obj:
        if order_obj.pay_status == 1:
            order_user = order_obj.username
            order_id=order_obj.order_id
            proxy_username=order_user+"_"+order_id[0:8]
            variant_obj = Variant.objects.filter(id=order_obj.variant_id).first()
            if variant_obj:
                server_group = variant_obj.server_group
                acl_group = variant_obj.acl_group
                cart_step = order_obj.cart_step
                server_obj = ServerGroup.objects.filter(id=server_group.id).first()
                if server_obj:
                    servers = server_obj.servers.all()
                    for server in servers:
                        cidr_info = server.get_cidr_info()
                        for cidr in cidr_info:
                            Stock = ProxyStock.objects.filter(acl_group=acl_group.id, cidr=cidr['id'],
                                                              variant_id=variant_obj.id).first()
                            create_count = 0
                            while Stock.cart_stock:
                                for i in range(order_obj.product_quantity):
                                    server_api_url="http://{}:65533".format(server.ip)
                                    kaxy_client=KaxyClient(server_api_url)
                                    proxy_info=kaxy_client.create_user_by_prefix(proxy_username,order_user)

                                    proxy_obj = Proxy.objects.create(server_id=server.id, acl_group=acl_group,
                                                                     order_id=order_id)
                                    Stock.ip_stock -= 1
                                    if (i + 1) % cart_step == 0:
                                        Stock.cart_stock -= 1
                                    Stock.save()