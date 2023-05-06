import datetime
import pytz
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from apps.core.permissions import IsSuperUser
from apps.core.permissions import IsAuthenticated
from apps.core.json_response import SuccessResponse, ErrorResponse
from apps.core.viewsets import ComModelViewSet
from apps.orders.models import Orders
from apps.orders.serializers import OrdersSerializer, OrdersUpdateSerializer, \
    OrdersStatusSerializer, ProxyListSerializer
from apps.proxy_server.models import Proxy
from rest_framework.views import APIView
from .services import verify_webhook, shopify_order, get_checkout_link, renew_proxy_by_order, get_renew_checkout_link
import logging
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from apps.orders.services import create_proxy_by_order
from apps.rewards.models import CouponCode, PointRecord
from apps.users.models import User, InviteLog
from apps.utils.kaxy_handler import KaxyClient


class OrdersApi(ComModelViewSet):
    """
    订单接口
    list:获取订单列表
    create:创建订单
    retrieve:获取订单详情
    update:更新订单
    destroy:删除订单
    get_status:获取订单状态
    reset_proxy_password:重置代理密码
    update_proxy_expired_at:更新代理过期时间
    order_renew_checkout:订单续费结账
    reset_proxy:重置代理
    """
    queryset = Orders.objects.all()
    serializer_class = OrdersSerializer
    update_serializer_class = OrdersUpdateSerializer
    get_status_serializer_class = OrdersStatusSerializer
    search_fields = ('order_id', 'username', 'uid', 'product_name')
    filterset_fields = ('order_id', 'username', 'uid', 'product_name', 'product_type')
    permission_classes = [IsAuthenticated]

    # def get_permissions(self):
    #     if self.action == 'list':
    #         self.permission_classes = [AllowAny]
    #     return super().get_permissions()

    # @swagger_auto_schema(operation_description="获取订单状态", responses={200: OrdersStatusSerializer},
    #                      query_serializer=OrdersStatusSerializer)
    def list(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            self.queryset=self.queryset.filter(pay_status=1)
        return super().list(request, *args, **kwargs)

    @action(methods=['get'], detail=False, url_path='get_status', url_name='get_status')
    def get_status(self, request):
        # 用于前端轮询订单状态
        request_data = request.query_params.dict()
        order_id= request_data.get('order_id', None)
        if not order_id:
            return ErrorResponse(data={}, msg="订单号不能为空")
        order = Orders.objects.filter(order_id=order_id)
        if not order.exists():
            return ErrorResponse(data={}, msg="订单不存在")
        order = order.first()
        if order.pay_status == 1:
            return SuccessResponse(data={"status": 1}, msg="订单已支付")
        return SuccessResponse(data={"status": 0}, msg="订单未支付")

    def retrieve(self, request, *args, **kwargs):
        proxy = Proxy.objects.filter(order_id=kwargs.get('pk'))
        proxy_list = []
        if proxy.exists():
            proxy_data = proxy.all()
            serializer = ProxyListSerializer(proxy_data, many=True)
            proxy_list = serializer.data
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return SuccessResponse(data={"order": serializer.data, "proxy_list": proxy_list}, msg="获取成功")

    @action(methods=['post'], detail=True, url_path='reset_proxy_password', url_name='reset_proxy_password',
            permission_classes=[IsSuperUser])
    def reset_proxy_password(self, request, *args, **kwargs):
        order_id = kwargs.get('pk')
        server_ip = Proxy.objects.filter(order_id=order_id).distinct('server_ip').all()
        username = Proxy.objects.filter(order_id=order_id).distinct('username').all()
        if server_ip.exists() and username.exists():
            for s_ip in server_ip:
                for u in username:
                    ip_ = s_ip.server_ip
                    username_ = u.username
                    client = KaxyClient(ip_)
                    proxy_list = client.update_user(username_)
                    for p in proxy_list:
                        proxy_ip, port, username, password = p.split(':')
                        proxy = Proxy.objects.filter(ip=proxy_ip, username=username).first()
                        if proxy:
                            proxy.password = password
                            proxy.save()

        return SuccessResponse(data={}, msg="代理密码重置成功")

    @action(methods=['post'], detail=True, url_path='update_proxy_expired_at', url_name='update_proxy_expired_at',
            permission_classes=[IsSuperUser])
    def update_proxy_expired_at(self, request, *args, **kwargs):
        order_id = kwargs.get('pk')
        expired_at = request.data.get('expired_at', None)
        if not expired_at:
            return SuccessResponse(data={}, msg="过期时间不能为空")
        # 时间戳转换
        try:
            expired_at = datetime.datetime.fromtimestamp(int(expired_at) // 1000).replace(tzinfo=datetime.timezone.utc)
        except Exception as e:
            return ErrorResponse(data={}, msg="过期时间格式错误")
        order = Orders.objects.filter(id=order_id)
        if order.exists():
            order = order.first()
            proxy = Proxy.objects.filter(order_id=order_id)
            if proxy.exists():
                for p in proxy.all():
                    if p.expired_at > expired_at:
                        return ErrorResponse(data={}, msg="代理过期时间不能小于当前时间")
                    p.expired_at = expired_at
                    p.save()
            order.expired_at = expired_at
            order.save()
        else:
            return ErrorResponse(data={}, msg="订单不存在")
        return SuccessResponse(data={}, msg="代理过期时间更新成功")

    @action(methods=['post'], detail=True, url_path='reset_proxy', url_name='reset_proxy')
    def reset_proxy(self, request, *args, **kwargs):
        order_pk = kwargs.get('pk')
        order = Orders.objects.filter(id=order_pk)

        if order.exists():
            order = order.first()
            order_id = order.order_id
            # 删除代理
            Proxy.objects.filter(order_id=order_pk).all().delete()
            # 重新创建代理
            create_proxy_by_order(order_id)
        else:
            return ErrorResponse(data={}, msg="订单不存在")
        return SuccessResponse(data={}, msg="代理重置成功")

    @action(methods=['get'], detail=True, url_path='get_proxy_detail', url_name='get_proxy_detail')
    def get_proxy_detail(self, request, *args, **kwargs):
        order_id = kwargs.get('pk')
        proxy = Proxy.objects.filter(order_id=order_id)
        proxy_list = []
        if proxy.exists():
            proxy_data = proxy.all()
            serializer = ProxyListSerializer(proxy_data, many=True)
            proxy_list = serializer.data
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return SuccessResponse(data={"order": serializer.data, "proxy_list": proxy_list}, msg="获取成功")

    @action(methods=['post'], detail=True, url_path='order-renew-checkout', url_name='order-renew-checkout')
    def order_renew_checkout(self, request, *args, **kwargs):
        order_pk = kwargs.get('pk')
        if request.user.is_superuser:
            return ErrorResponse(data={}, msg="管理员无法购买")
        order = Orders.objects.filter(id=order_pk)
        if not order.exists():
            return ErrorResponse(data={}, msg="Order does not exist.")  # 订单不存在
        order = order.first()
        order_id = order.order_id
        if order.expired_at < datetime.datetime.now(tz=datetime.timezone.utc):
            return ErrorResponse(data={}, msg="The order has expired, please place a new order.")  # 订单已过期，请下新订单
        checkout_url, order_id = get_renew_checkout_link(order_id=order_id)
        return SuccessResponse(data={"checkout_url": checkout_url, "order_id": order_id}, msg="订单生成成功")


class OrderCallbackApi(APIView):
    """
    订单回调接口
    """

    def get(self, request):
        # 通过pix脚本回调
        # 功能有限，暂不使用
        return SuccessResponse(data={}, msg="回调成功")


@method_decorator(csrf_exempt, name="dispatch")
class ShopifyWebhookApi(APIView):
    """
    shopify回调接口
    """

    def post(self, request):
        # todo 订单回调
        # webhook回调
        # 收到回调后，调用shopify接口，查询订单状态，如果是已付款，则更新本地订单状态
        # 验证签名
        if not verify_webhook(request):
            return ErrorResponse(data={}, msg="签名验证失败")
        # shopify订单回调
        order_info = shopify_order(request.data)
        shopify_order_info = order_info.get("order")
        financial_status = shopify_order_info.get('financial_status')
        if financial_status == 'paid':
            shpify_order_id = order_info.get('order_id')
            shopify_order_number = shopify_order_info.get('order_number')
            pay_amount = shopify_order_info.get('total_price')
            discount_codes = order_info.get('discount_codes')
            renewal_status = order_info.get("renewal", "0")
            order_id = order_info.get('order_id')
            # 更新订单
            order = Orders.objects.filter(order_id=order_id).first()
            if order:
                if renewal_status == "1":
                    order.pay_amount = order.pay_amount + pay_amount
                order.pay_amount = pay_amount  # 支付金额
                order.pay_status = 1  # 已支付
                order.shopify_order_id = shpify_order_id  # shopify订单id
                order.shopify_order_number = shopify_order_number  # shopify订单号
                order.save()
                logging.error("aaaaaa")
            # 生成代理，修改订单状态
            if renewal_status == "1":
                order.renew_status = 1
                order.save()
                # 续费
                order_process_ret = renew_proxy_by_order(order_id)
            else:
                # 新订
                order_process_ret = create_proxy_by_order(order_id)
                logging.error(order_process_ret)
            if order_process_ret:
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
                        inviter_user = User.objects.filter(id=invite_log.inviter_uid).first()
                        if inviter_user:
                            inviter_user.reward_points += int(
                                float(order.pay_amount) * float(settings.INVITE_REBATE_RATE))  # 奖励积分
                            inviter_user.save()
                            # 创建积分变动记录
                            PointRecord.objects.create(uid=inviter_user.id, point=int(
                                float(order.pay_amount) * float(settings.INVITE_REBATE_RATE)),
                                                       reason=PointRecord.REASON_DICT["invite_buy"])
                # 增加用户等级积分
                order_user.level_points += int(float(order.pay_amount) * float(settings.BILLING_RATE))  # 等级积分
                order_user.save()
                # 更新用户等级
                order_user.update_level()
                # fixme 发送邮件
                # send_order_email(order_id)

            else:
                # fixme 发送邮件
                # send_order_email(order_id)
                pass
        else:
            logging.error("订单未支付", order_info)

        return SuccessResponse()


class CheckoutApi(APIView):
    """
    订单结算接口
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        # 生成订单
        if request.user.is_superuser:
            return ErrorResponse(data={}, msg="管理员无法购买")
        checkout_url, order_id = get_checkout_link(request)
        if not checkout_url:
            return ErrorResponse(data={}, msg="订单生成失败")
        return SuccessResponse(data={"checkout_url": checkout_url, "order_id": order_id}, msg="订单生成成功")

    def get(self, request, *args, **kwargs):
        order_id = request.query_params.get('order_id', None)
        order = Orders.objects.filter(order_id=order_id)
        if order.exists():
            order = order.first()
            if order.pay_status == 1:
                return SuccessResponse(data={}, msg="订单已支付")
            elif order.pay_status == 0:
                return ErrorResponse(data={}, msg="订单未支付")
            else:
                return ErrorResponse(data={}, msg="订单支付失败")
        else:
            return ErrorResponse(data={}, msg="订单不存在")
