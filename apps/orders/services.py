import datetime
import hmac
import hashlib
import base64
import ipaddress
import logging
import re
import threading
import time

from apps.utils.shopify_handler import ShopifyClient
from django.conf import settings
from apps.rewards.models import LevelCode, CouponCode, PointRecord
from .models import Orders
from apps.proxy_server.models import Server, Proxy, ServerGroup, ProxyStock, Acls, ProductStock, ServerCidrThrough
from apps.products.models import Product, Variant
from apps.utils.kaxy_handler import KaxyClient
from apps.users.models import User, InviteLog
from apps.users.services import send_email_api
from django.utils import timezone
from django.db.models import Q
from ipaddress import ip_network
from apps.products.services import get_available_cidrs
from django.core.cache import cache

lock_id = "create_order"


def get_white_acl(acl_ids):
    """
    使用黑名单实现白名单
    """
    white_acl = Acls.objects.filter(~Q(id__in=acl_ids)).all()
    white_acl_list = {"ids": [], "acl_value": []}
    for acl in white_acl:
        white_acl_list.get("ids").append(acl.id)
        white_acl_list.get("acl_value").append(acl.acl_value)
    return white_acl_list


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


def change_shopify_order_info(order_info):
    shop_url = settings.SHOPIFY_SHOP_URL
    api_key = settings.SHOPIFY_API_KEY
    api_scert = settings.SHOPIFY_API_SECRET
    private_app_password = settings.SHOPIFY_APP_KEY
    shopify_client = ShopifyClient(shop_url, api_key, api_scert, private_app_password)
    shopify_client.update_order(order_info)


def shopify_order(data):
    """
    Format the order data to be sent to the client
    """
    discount_codes = []
    for discount in data["discount_codes"]:
        discount_codes.append(discount["code"])
    return_data = {
        "shopify_order_id": str(data["id"]),
        "order": {
            "created_at": data["created_at"],
            "total_price": data["total_price"],  # 总价
            "total_weight": data["total_weight"],
            "currency": data["currency"],
            "financial_status": data["financial_status"],  # 支付状态
            "order_number": data["order_number"],  # 订单号
            "order_status_url": data["order_status_url"],
            "line_items": data["line_items"],
        },
        "note": data["note"],
        "discount_codes": discount_codes,
        "note_attributes": data["note_attributes"],
        "email": data["customer"]["email"],

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
    product_obj = Product.objects.filter(id=order_info_dict["product_id"]).first()
    if product_obj:
        order_info_dict["product_name"] = product_obj.product_name
    option_selected = request.data.get("option_selected", {})
    acl_selected = option_selected.get("acl_selected", [])
    variant_option1 = option_selected.get("option1", "")
    variant_option2 = option_selected.get("option2", "")
    variant_option3 = option_selected.get("option3", "")
    variant_obj = Variant.objects.filter(product=order_info_dict["product_id"], variant_option1=variant_option1,
                                         variant_option2=variant_option2, variant_option3=variant_option3)
    acl_variant_ids = Acls.objects.filter(id__in=acl_selected).all().values_list("shopify_variant_id", flat=True)
    # 查询产品信息
    variant_obj = variant_obj.first()
    if variant_obj:
        order_info_dict["variant_id"] = variant_obj.shopify_variant_id
        order_info_dict["product_price"] = variant_obj.variant_price
        order_info_dict["local_variant_id"] = variant_obj.id
        order_info_dict["variant_name"] = variant_obj.variant_name
        proxy_time = variant_obj.proxy_time
        order_info_dict["product_total_price"] = order_info_dict["product_price"] * int(
            order_info_dict["product_price"])
        order_info_dict["product_type"] = Product.objects.filter(
            id=order_info_dict["product_id"]).first().product_collections.first().id
        expired_at = datetime.datetime.now(timezone.utc) + datetime.timedelta(days=proxy_time)
        order_info_dict["expired_at"] = expired_at
        order_info_dict["proxy_num"] = order_info_dict["product_quantity"]
        order_info_dict["proxy_time"] = proxy_time
        order_info_dict["option1"] = variant_option1
        order_info_dict["option2"] = variant_option2
        order_info_dict["option3"] = variant_option3
        order_info_dict["acl_selected"] = ",".join(map(str, acl_selected))
        new_order = Orders.objects.create(**order_info_dict)
        order_id = new_order.order_id
        if level_code_obj:
            code = level_code_obj.code
        else:
            code = None
        cart_quantity_pairs = ["{}:{}".format(order_info_dict["variant_id"], order_info_dict["product_quantity"])]
        # 添加acl_variant_id
        for acl_variant_id in acl_variant_ids:
            cart_quantity_pairs.append("{}:{}".format(acl_variant_id, order_info_dict["product_quantity"]))
        check_info = {
            "cart_quantity_pairs": cart_quantity_pairs,
            "discount": code,
            "email": user.email,
            "note": "order_id_{}".format(order_id),
            'attributes': {"order_id": order_id, "renewal": request.data.get("renewal", "0")},
            "ref": "mentosproxy_web",
            "access_token": "b1eadac0d1d5d003be6ed95eb9997022"
        }
        checkout_link = ShopifyClient.get_checkout_link(settings.SHOPIFY_SHOP_URL, check_info)
        new_order.checkout_url = checkout_link
        new_order.save()
        return checkout_link, order_id
    else:
        return None, None


def get_renew_checkout_link(order_id, request):
    user = request.user
    user_level = user.level
    level_code_obj = LevelCode.objects.filter(level=user_level).first()

    order_obj = Orders.objects.filter(order_id=order_id).first()
    if order_obj:
        checkout_link = order_obj.checkout_url
        renew_checkot_url = re.sub(r'attributes\[renewal\]=\d', 'attributes[renewal]=1', checkout_link)
        if level_code_obj:
            code = level_code_obj.code
            renew_checkot_url = re.sub(r'discount=\w+', 'discount={}'.format(code), renew_checkot_url)
        order_obj.shopify_order_number = None
        order_obj.save()
        return renew_checkot_url, order_id
    else:
        return None, None


def create_proxy_by_order_obj(order_obj):
    """
    根据订单创建代理
    """
    msg = ""
    proxy_list = []
    proxy_id_list = []
    if order_obj:
        if order_obj.pay_status != 1:
            logging.info('订单未支付')
            msg = '订单未支付'
            return False, msg, proxy_id_list
        if order_obj.expired_at < datetime.datetime.now(timezone.utc):
            logging.info('订单过期')
            msg = 'order expired'
            return False, msg, proxy_id_list
        order_id = order_obj.order_id
        lock_id = 'create_proxy_by_id_{}'.format(order_id)
        with cache.lock(lock_id):
            order_user_obj = User.objects.filter(id=order_obj.uid).first()
            order_user = order_obj.username
            user_email = order_user_obj.email
            order_id = order_obj.order_id
            order_pk = order_obj.id
            product_name = order_obj.product_name
            now = str(int(time.time()))[-4:]
            proxy_username = "{}{}{}".format(now, order_user, order_id)[:15]
            acl_ids = order_obj.acl_selected.split(",")
            white_acl_list = get_white_acl(acl_ids)
            acl_value = "\n".join(white_acl_list.get("acl_value"))
            proxy_expired_at = order_obj.expired_at  # 代理过期时间
            product_quantity = order_obj.product_quantity
            variant_obj = Variant.objects.filter(id=order_obj.local_variant_id).first()  # 获取订单对应的套餐
            if variant_obj:
                cart_step = variant_obj.cart_step
                cidr_list = []
                for cidr in variant_obj.cidrs.all():
                    cidr_list.append(cidr.id)
                available_cidrs = get_available_cidrs(acl_ids, cidr_list, cart_step)
                if len(available_cidrs) * cart_step < product_quantity:
                    logging.info('可用子网数量不足')
                    msg = "可用子网数量不足"
                    return False, msg, proxy_id_list
                if available_cidrs:
                    for cidr_str, stock_infos in available_cidrs.items():
                        error_cnt = 0
                        stocks = []
                        stock_ids = []
                        for stock_info in stock_infos:
                            stocks.append(stock_info[0])
                            stock_ids.append(stock_info[0].id)
                        stock_ids_str = ",".join([str(stock_id) for stock_id in stock_ids])
                        cidr_id = stocks[0].cidr.id
                        logging.info("cidr_id:{}".format(cidr_id))
                        server_ip = ServerCidrThrough.objects.filter(cidr_id=cidr_id).first().server.ip
                        kaxy_client = KaxyClient(server_ip)
                        if not kaxy_client.status:
                            msg = "服务器{}创建代理失败:{}".format(server_ip, "无法连接服务器")
                            logging.info(msg)
                            return False, msg, proxy_id_list
                        try:
                            proxy_info = kaxy_client.create_user_acl_by_prefix(proxy_username, cidr_str, acl_value)
                        except Exception as e:
                            msg = "服务器{}创建代理失败:{}".format(server_ip, e)
                            logging.exception(e)
                            return False, msg, proxy_id_list
                        for proxy_i in proxy_info["proxy"]:
                            ip, port, user, password = proxy_i.split(":")
                            p = Proxy.objects.create(ip=ip, port=port, username=user, password=password,
                                                     server_ip=server_ip,
                                                     order=order_obj, expired_at=proxy_expired_at, user=order_user_obj,
                                                     ip_stock_ids=stock_ids_str, subnet=cidr_str,
                                                     acl_ids=",".join(acl_ids),local_variant_id=order_obj.local_variant_id,cidr_id=cidr_id)
                            proxy_id_list.append(p.id)
                        proxy_list.extend(proxy_info["proxy"])
                        for stock in stocks:
                            stock.remove_available_subnet(cidr_str)
                            logging.info("stock_id:{} remove subnet:{}".format(stock.id, cidr_str))
                            stock.cart_stock -= 1
                            stock.ip_stock -= len(proxy_info["proxy"])
                            stock.save()
                            error_cnt = 0
                        else:
                            error_cnt += 1
                        if len(proxy_list) >= product_quantity:
                            # 代理数量已经够了
                            break
                if proxy_list:
                    # 更新订单状态
                    order_obj.order_status = 4
                    order_obj.delivery_status = 1
                    order_obj.delivery_num = len(proxy_list)
                    order_obj.save()
                    variant_obj.save()  # 更新套餐库存
                    email_template = settings.EMAIL_TEMPLATES.get("delivery")
                    subject = email_template.get('subject')
                    html_message = email_template.get('html').replace('{{order_id}}', str(order_pk)).replace(
                        '{{proxy_number}}', str(len(proxy_list))).replace('{{product}}', str(product_name)).replace(
                        '{{proxy_expired_at}}', proxy_expired_at.strftime('%Y-%m-%d %H:%M:%S'))
                    from_email = email_template.get('from_email')
                    send_success = send_email_api(user_email, subject, from_email, html_message)
                    logging.info("order_id:{} delivery success".format(order_pk))
                    return True, '创建代理成功', proxy_id_list
            else:
                logging.info('套餐不存在')
                msg = '套餐不存在'
                return False, msg, proxy_id_list
    else:
        logging.info('订单不存在')
        msg = '订单不存在'
    logging.info("order process fail,msg:{}".format(msg))
    return False, msg, proxy_id_list


def create_proxy(filter_dict):
    order_obj = Orders.objects.filter(**filter_dict).first()
    return create_proxy_by_order_obj(order_obj)


def renew_proxy_by_order(order_id):
    """
    根据订单续费代理
    """
    order_obj = Orders.objects.filter(order_id=order_id, renew_status=1).first()
    if order_obj:
        proxies = Proxy.objects.filter(order=order_obj).all()
        for proxy in proxies:
            proxy.expired_at += datetime.timedelta(days=order_obj.proxy_time)
            proxy.save()
        order_obj.expired_at += datetime.timedelta(days=order_obj.proxy_time)
        order_obj.save()
        return True, ''
    return False, '订单不存在无法续费'


# 创建发货线程
def webhook_handle_thread(order_info, order_id):
    # 因调用kaxy接口时间较长，所以使用线程处理,指定线程名称，如果有相同名称的线程，不会创建新的线程
    thred_name = 'webhook_handle_' + str(order_id)
    threads = threading.enumerate()
    for thread in threads:
        if thread.name == thred_name:
            return False
    t = threading.Thread(target=webhook_handle, args=(order_info,), name=thred_name)
    t.start()
    return True


def webhook_handle(order_info):
    # shopify订单回调
    try:
        shopify_order_info = order_info.get("order")
        financial_status = shopify_order_info.get('financial_status')
        if financial_status == 'paid':
            shpify_order_id = order_info.get('shopify_order_id')
            shopify_order_number = shopify_order_info.get('order_number')
            pay_amount = shopify_order_info.get('total_price')
            discount_codes = order_info.get('discount_codes')
            renewal_status = order_info.get("renewal", "0")
            order_id = order_info.get('order_id')
            email = order_info.get('email')
            # 更新订单
            order = Orders.objects.filter(order_id=order_id).first()
            if order:
                if renewal_status == "1":
                    order.pay_amount = float(order.pay_amount) + float(pay_amount)
                    order.renew_status += 1
                order.pay_amount = float(pay_amount)  # 支付金额
                order.pay_status = 1  # 已支付
                order.shopify_order_id = shpify_order_id  # shopify订单id
                order.shopify_order_number = shopify_order_number  # shopify订单号
                order.save()
                user_email = User.objects.filter(id=order.uid).first().email

                # 生成代理，修改订单状态
                if renewal_status == "1":
                    # 续费
                    order_process_ret, msg = renew_proxy_by_order(order_id)
                else:
                    # 新订
                    # if user_email.lower() != email.lower():
                    #     logging.warning("email not match: %s, %s order_id: %s" % (user_email,email,order_id))
                    #     logging.info("order process fail")
                    #     order_info = {"id": shpify_order_id, "tags": "delivery_fail", "note": "邮箱不匹配"}
                    #     t1 = threading.Thread(target=change_shopify_order_info, args=(order_info,)).start()
                    #     return
                    filter_dict = {"order_id": order_id, "pay_status": 1}
                    order_process_ret, msg, proxy_id_list = create_proxy(filter_dict)
                Orders.objects.filter(order_id=order_id).update(shopify_order_number=shopify_order_number)
                if order_process_ret:
                    order_info = {"id": shpify_order_id, "tags": "delivered"}
                    if renewal_status == "1":
                        order_info["tags"] += ",renew"
                    t1 = threading.Thread(target=change_shopify_order_info, args=(order_info,)).start()
                    # 修改优惠券状态
                    for discount_code in discount_codes:
                        coupon = CouponCode.objects.filter(code=discount_code).first()
                        if coupon:
                            coupon.used_code()
                    # 增加邀请人奖励积分
                    order_user = User.objects.filter(id=order.uid).first()
                    if order_user:
                        invite_log = InviteLog.objects.filter(uid=order.uid).first()
                        if invite_log:
                            # 查询邀请人
                            inviter_user = User.objects.filter(id=invite_log.inviter_user_id).first()
                            if inviter_user:
                                inviter_user.reward_points += int(
                                    float(order.product_total_price) * float(settings.INVITE_REBATE_RATE))  # 奖励积分
                                inviter_user.save()
                                # 创建积分变动记录
                                PointRecord.objects.create(uid=inviter_user.id, point=int(
                                    float(order.product_total_price) * float(settings.INVITE_REBATE_RATE)),
                                                           reason=PointRecord.REASON_DICT["invite_buy"])
                                logging.info("invite user reward points success")
                    # 增加用户等级积分
                    order_user.level_points += int(
                        float(order.product_total_price) * float(settings.BILLING_RATE))  # 等级积分
                    order_user.save()
                    # 更新用户等级
                    order_user.update_level()
                    # fixme 发送邮件
                    # send_order_email(order_id)
                else:
                    # fixme 发送邮件
                    # send_order_email(order_id)
                    logging.info("order process fail")
                    order_info = {"id": shpify_order_id, "tags": "delivery_fail", "note": msg}
                    t1 = threading.Thread(target=change_shopify_order_info, args=(order_info,)).start()
                    order.fail_reason = msg
                    order.save()

            else:
                logging.info("order not exist")
                order_info = {"id": shpify_order_id, "tags": "delivery_fail", "note": "订单不存在"}
                t1 = threading.Thread(target=change_shopify_order_info, args=(order_info,))
    except Exception as e:
        logging.exception(e)


def delete_proxy_by_order_pk(order_id):
    """
    删除订单所有代理
    """
    for p in Proxy.objects.filter(order_id=order_id).all():
        p.delete()
    return True


def update_orders():
    orders = Orders.objects.filter(order_status=1).all()
