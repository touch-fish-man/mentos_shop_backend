import datetime

from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action

from apps.core.json_response import SuccessResponse, ErrorResponse
from apps.core.viewsets import ComModelViewSet
from apps.orders.models import Orders
from apps.orders.serializers import OrdersSerializer, OrdersCreateSerializer, OrdersUpdateSerializer, \
    OrdersStatusSerializer, ProxyListSerializer
from apps.proxy_server.models import Proxy
from rest_framework.views import APIView
from .services import verify_webhook, shopify_order, get_checkout_link
import logging
from django.utils.decorators import method_decorator
from apps.orders.task import del_order_proxy,email_notification
from django.views.decorators.csrf import csrf_exempt


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
    """
    queryset = Orders.objects.all()
    serializer_class = OrdersSerializer
    create_serializer_class = OrdersCreateSerializer
    update_serializer_class = OrdersUpdateSerializer
    get_status_serializer_class = OrdersStatusSerializer
    search_fields = ('order_id', 'username', 'uid', 'product_name')
    filterset_fields = ('order_id', 'username', 'uid', 'product_name')

    # @swagger_auto_schema(operation_description="获取订单状态", responses={200: OrdersStatusSerializer},
    #                      query_serializer=OrdersStatusSerializer)
    @action(methods=['get'], detail=False, url_path='get_status', url_name='get_status')
    def get_status(self, request):
        # 用于前端轮询订单状态
        serializer = self.get_status_serializer_class(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return SuccessResponse(data=serializer.data, msg="获取成功")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, request=request)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        del_order_proxy(serializer.data['order_id'])
        email_notification(order_id=serializer.data['order_id'])
        return SuccessResponse(data=serializer.data, msg="新增成功")

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

    @action(methods=['post'], detail=True, url_path='reset_proxy_password', url_name='reset_proxy_password')
    def reset_proxy_password(self, request, *args, **kwargs):
        order_id = kwargs.get('pk')
        new_password = request.data.get('new_password', None)
        if not new_password:
            return SuccessResponse(data={}, msg="新密码不能为空")
        proxy = Proxy.objects.filter(order_id=order_id)
        if proxy.exists():
            for p in proxy.all():
                p.password = new_password
                p.save()
                # todo 重置代理密码
        return SuccessResponse(data={}, msg="代理密码重置成功")

    @action(methods=['post'], detail=True, url_path='update_proxy_expired_at', url_name='update_proxy_expired_at')
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
                    # todo 重置代理密码
            order.expired_at = expired_at
            order.save()
        else:
            return ErrorResponse(data={}, msg="订单不存在")
        return SuccessResponse(data={}, msg="代理过期时间更新成功")

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


class OrderCallbackApi(APIView):
    """
    订单回调接口
    """

    def get(self, request):
        # todo 订单回调
        # 通过pix脚本回调
        # 收到回调后，调用shopify接口，查询订单状态，如果是已付款，则更新本地订单状态
        # 验证签名
        logging.error(request.query_params)
        return SuccessResponse(data={}, msg="回调成功")


@method_decorator(csrf_exempt, name="dispatch")
class ShopifyWebhookApi(APIView):
    """
    shopify回调接口
    """

    def post(self, request):
        # todo 订单回调
        # 通过pix脚本回调
        # 收到回调后，调用shopify接口，查询订单状态，如果是已付款，则更新本地订单状态
        # 验证签名
        if not verify_webhook(request):
            return ErrorResponse(data={}, msg="签名验证失败")
        logging.error(request.data)
        # shopify订单回调
        shopify_order(request.data)
        return SuccessResponse()


class CheckoutApi(APIView):
    """
    订单结算接口
    """

    def post(self, request, *args, **kwargs):
        # 生成订单
        user = request.user
        if user.is_authenticated:
            checkout_url, order_id = get_checkout_link(request)
            if not checkout_url:
                return ErrorResponse(data={}, msg="订单生成失败")
            return SuccessResponse(data={"checkout_url": checkout_url, "order_id": order_id}, msg="订单生成成功")
        else:
            return ErrorResponse(data={}, msg="用户未登录")

    def get(self, request, *args, **kwargs):
        order_id = request.query_params.get('order_id', None)
        user = request.user
        if user.is_authenticated:
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
        else:
            return ErrorResponse(data={}, msg="用户未登录")
