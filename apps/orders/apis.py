import datetime

from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action

from apps.core.json_response import SuccessResponse,ErrorResponse
from apps.core.viewsets import ComModelViewSet
from apps.orders.models import Orders
from apps.orders.serializers import OrdersSerializer, OrdersCreateSerializer, OrdersUpdateSerializer, \
    OrdersStatusSerializer, ProxyListSerializer
from apps.proxy_server.models import Proxy






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
    search_fields = ('order_id', 'username', 'uid', 'product_name', 'status')
    filter_fields = ('order_id', 'username', 'uid', 'product_name', 'status')

    @swagger_auto_schema(operation_description="获取订单状态", responses={200: OrdersStatusSerializer},
                         query_serializer=OrdersStatusSerializer)
    @action(methods=['get'], detail=False, url_path='get_status', url_name='get_status')
    def get_status(self, request):
        serializer = self.get_status_serializer_class(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return SuccessResponse(data=serializer.data, msg="获取成功")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data,request=request)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
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
            expired_at = datetime.datetime.fromtimestamp(int(expired_at)).replace(tzinfo=datetime.timezone.utc)
        except Exception as e:
            return ErrorResponse(data={}, msg="过期时间格式错误")
        order=Orders.objects.filter(id=order_id)
        if order.exists():
            order=order.first()
            proxy = Proxy.objects.filter(order_id=order_id)
            if proxy.exists():
                for p in proxy.all():
                    if p.expired_at > expired_at:
                        return ErrorResponse(data={}, msg="代理过期时间不能小于当前时间")
                    p.expired_at = expired_at
                    p.save()
                    # todo 重置代理密码
            order.expired_at=expired_at
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
    
