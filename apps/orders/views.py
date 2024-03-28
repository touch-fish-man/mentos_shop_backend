import datetime
import threading
import time

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
from .services import verify_webhook, shopify_order, get_checkout_link, get_renew_checkout_link, webhook_handle_thread, \
    create_proxy, delete_proxy_by_order_pk
import logging
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from apps.utils.kaxy_handler import KaxyClient
from apps.products.models import Product, Variant
from django.core.exceptions import ObjectDoesNotExist

from ..core.cache_lock import memcache_lock


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
    queryset = Orders.objects.all().order_by('-updated_at')
    serializer_class = OrdersSerializer
    update_serializer_class = OrdersUpdateSerializer
    get_status_serializer_class = OrdersStatusSerializer
    search_fields = ('id', 'order_id', 'shopify_order_number', 'username', 'uid', 'product_name', 'product_type')
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
            self.queryset = self.queryset.filter(pay_status=1, uid=str(request.user.id))
        return super().list(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        # 后台删除订单,处理删除超时的问题
        instance = self.get_object()
        t1 = threading.Thread(target=self.perform_destroy, args=(instance,)).start()

        return SuccessResponse(data={}, msg="删除成功")

    @action(methods=['get'], detail=False, url_path='get_status', url_name='get_status')
    def get_status(self, request):
        # 用于前端轮询订单状态
        request_data = request.query_params.dict()
        order_id = request_data.get('order_id', None)
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
        server_ip = Proxy.objects.filter(order_id=order_id).values_list('server_ip', flat=True).distinct()
        username = Proxy.objects.filter(order_id=order_id).values_list('username', flat=True).distinct()
        if len(server_ip) and len(username):
            for s_ip in server_ip:
                for u in username:
                    ip_ = s_ip.server_ip
                    username_ = u.username
                    client = KaxyClient(ip_)
                    if not client.status:
                        return ErrorResponse(data={}, msg="服务器{}连接失败,请检查服务器状态".format(ip_))
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
        expired_at_timestamp = request.data.get('expired_at', None)

        if not expired_at_timestamp:
            return ErrorResponse(data={}, msg="过期时间不能为空")

        try:
            expired_at = datetime.datetime.fromtimestamp(int(expired_at_timestamp) // 1000).replace(
                tzinfo=datetime.timezone.utc)
        except ValueError:
            return ErrorResponse(data={}, msg="过期时间格式错误")
        now = datetime.datetime.now(datetime.timezone.utc)
        if expired_at < now:
            return ErrorResponse(data={}, msg="过期时间不能小于当前时间")

        try:
            order = Orders.objects.get(id=order_id)
        except ObjectDoesNotExist:
            return ErrorResponse(data={}, msg="订单不存在")

        Proxy.objects.filter(order_id=order.id).update(expired_at=expired_at)
        order.expired_at = expired_at
        order.save()

        return SuccessResponse(data={}, msg="代理过期时间更新成功")

    @action(methods=['post'], detail=True, url_path='reset_proxy', url_name='reset_proxy')
    def reset_proxy(self, request, *args, **kwargs):
        order_pk = kwargs.get('pk')
        order = Orders.objects.filter(id=order_pk)

        if order.exists():
            order = order.first()
            # 删除代理
            lock_id = "reset_proxy"
            if memcache_lock(lock_id, order_pk).is_locked():
                return ErrorResponse(data={}, msg="代理正在重置中,请稍后重试,根据代理数量不同,重置时间不同")
            from apps.proxy_server.tasks import reset_proxy_fn
            reset_proxy_fn.delay(order_pk, order.username)

        else:
            return ErrorResponse(data={}, msg="订单不存在")
        return SuccessResponse(data={}, msg="代理重置成功,请稍后刷新页面查看")

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

    @action(methods=['post'], detail=True, url_path='delete_proxy', url_name='delete_proxy')
    def delete_proxy(self, request, *args, **kwargs):
        order_id = kwargs.get('pk')
        # 异步删除代理
        t1 = threading.Thread(target=delete_proxy_by_order_pk, args=(order_id,)).start()
        return SuccessResponse(data={}, msg="删除成功")

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

        if not Variant.objects.filter(id=order.local_variant_id).first():
            return ErrorResponse(data={}, msg="The product does not exist, please place a new order.")  # 产品不存在，请下新订单
        checkout_url, order_id = get_renew_checkout_link(order_id=order_id, request=request)
        return SuccessResponse(data={"checkout_url": checkout_url, "order_id": order_id},
                               msg="get checkout url success")

    @action(methods=['post'], detail=False, url_path='one_key_reset', url_name='one_key_reset')
    def one_key_reset(self, request, *args, **kwargs):
        # 重置所有代理
        order_ids = request.data.get('order_ids', None)
        logging.info("order_ids:{}".format(order_ids))
        if not order_ids:
            return ErrorResponse(data={}, msg="订单id不能为空")
        try:
            order_ids = order_ids.split(',')
        except Exception as e:
            return ErrorResponse(data={}, msg="订单id格式错误")
        for order_id in order_ids:
            order = Orders.objects.filter(id=order_id).first()
            if order:
                # 删除代理
                for t in threading.enumerate():
                    if t.name == "onkey_reset_{}".format(order_id):
                        return ErrorResponse(data={}, msg="代理正在重置中,请稍后重试,根据代理数量不同,重置时间不同")
                Proxy.objects.filter(order_id=order_id).all().delete()
                filter_dict = {
                    'id': order_id,
                    'pay_status': 1,
                }
                # 重新创建代理
                t1 = threading.Thread(target=create_proxy, args=(filter_dict,),
                                      name="onkey_reset_{}".format(order_id)).start()

            else:
                return ErrorResponse(data={}, msg="订单不存在")
        return SuccessResponse(data={}, msg="重置成功")

    @action(methods=['get'], detail=True, url_path='check_proxy', url_name='check_proxy')
    def check_proxy(self, request, *args, **kwargs):
        order_pk = kwargs.get('pk')
        from apps.proxy_server.tasks import check_proxy_status
        check_proxy_status.delay(order_pk)
        return SuccessResponse(data={}, msg="代理状态检查中,请稍后刷新页面查看")


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
        #
        # webhook回调
        # 收到回调后，调用shopify接口，查询订单状态，如果是已付款，则更新本地订单状态
        # 验证签名
        if not verify_webhook(request):
            return ErrorResponse(data={}, msg="签名验证失败")
        # shopify订单回调
        order_info = shopify_order(request.data)
        logging.info("shopify订单回调信息:{}".format(order_info))
        shopify_order_info = order_info.get("order")
        financial_status = shopify_order_info.get('financial_status')
        order_id = order_info.get('order_id', "")
        if financial_status == 'paid':
            webhook_handle_thread(order_info, order_id)
        else:
            logging.error("订单未支付", order_info)

        return SuccessResponse()


@method_decorator(csrf_exempt, name="dispatch")
class ShopifyProductWebhookApi(APIView):
    """
    shopify产品回调接口
    """

    def post(self, request):
        #
        # webhook回调
        # 收到回调后，调用shopify接口，查询订单状态，如果是已付款，则更新本地订单状态
        # 验证签名
        if not verify_webhook(request):
            return ErrorResponse(data={}, msg="签名验证失败")
        logging.info("shopify产品回调信息:{}".format(request.data))
        from apps.orders.tasks import update_shopify_product
        update_shopify_product.delay()

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
