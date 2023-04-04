import hmac
import hashlib
import base64
from apps.utils.shopify_handler import ShopifyClient
from django.conf import settings
from apps.rewards.models import LevelCode
from .models import Orders

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
        }
    }
    if data.get("billing_address"):
        return_data["order"]["billing_address"] = {
            "city": data["billing_address"]["city"],
            "country": data["billing_address"]["country"],
            "country_code": data["billing_address"]["country_code"],
        }
    if data.get("shipping_address"):
        return_data["order"]["shipping_address"] = {
            "city": data["shipping_address"]["city"],
            "country": data["shipping_address"]["country"],
            "country_code": data["shipping_address"]["country_code"],
        }

    return return_data


def get_checkout_link(request):
    user=request.user
    user_level = user.level
    level_code_obj=LevelCode.objects.filter(level=user_level).first()
    # 创建订单
    order_info_dict={}
    order_info_dict["uid"]=user.id
    order_info_dict["username"]=user.username
    order_info_dict["product_id"]=request.data.get("product_id")
    order_info_dict["product_name"]=request.data.get("product_name")
    order_info_dict["product_price"]=request.data.get("product_price")
    order_info_dict["product_quantity"]=request.data.get("product_quantity")
    order_info_dict["product_total_price"]= float(request.data.get("product_price")) * int(request.data.get("product_quantity"))
    order_info_dict["variant_id"]=request.data.get("variant_id")
    order_info_dict["product_type"]=request.data.get("product_type")
    order_id = Orders.objects.create(**order_info_dict).order_id
    if level_code_obj:
        code=level_code_obj.code
    else:
        code=None
    cart_quantity_pairs=["{}:{}".format(request.data.get("variant_id"),request.data.get("product_quantity"))]
    check_info={
        "cart_quantity_pairs": cart_quantity_pairs,
        "discount": code,
        "email": request.data.get("email"),
        "note": request.data.get("note"),
        "ref": request.data.get("ref"),
    }
    checkout_link = ShopifyClient.get_checkout_link(settings.SHOPIFY_SHOP_URL, check_info)
    return checkout_link,order_id
