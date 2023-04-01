import datetime

from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
import pytz

from apps.core.json_response import SuccessResponse,ErrorResponse,LimitOffsetResponse
from apps.core.viewsets import ComModelViewSet
from apps.orders.models import Orders
from apps.orders.serializers import OrdersSerializer, OrdersCreateSerializer, OrdersUpdateSerializer, \
    OrdersStatusSerializer, ProxyListSerializer,UserOrdersSerializer,UserProxyListSerializer
from apps.proxy_server.models import ProxyList
from django.forms.models import model_to_dict
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from .tasks import add
from datetime import datetime, timedelta
from celery.result import AsyncResult
from django.utils.timezone import get_current_timezone



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
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return SuccessResponse(data=serializer.data, msg="新增成功")

    def retrieve(self, request, *args, **kwargs):
        proxy = ProxyList.objects.filter(order_id=kwargs.get('pk'))
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
        proxy = ProxyList.objects.filter(order_id=order_id)
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
        # 字符串时间格式转换datetime tzinfo
        try:
            expired_at = datetime.datetime.strptime(expired_at, "%Y-%m-%d %H:%M:%S").replace(
                tzinfo=datetime.timezone.utc)
        except Exception as e:
            return ErrorResponse(data={}, msg="过期时间格式错误")
        order=Orders.objects.filter(id=order_id)
        if order.exists():
            order=order.first()
            proxy = ProxyList.objects.filter(order_id=order_id)
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
        proxy = ProxyList.objects.filter(order_id=order_id)
        proxy_list = []
        if proxy.exists():
            proxy_data = proxy.all()
            serializer = ProxyListSerializer(proxy_data, many=True)
            proxy_list = serializer.data
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return SuccessResponse(data={"order": serializer.data, "proxy_list": proxy_list}, msg="获取成功")
    



class UserOrdersApi(ComModelViewSet):
    """
    用户订单接口
    list:获取订单列表
    create:创建订单
    retrieve:获取订单详情
    update:更新订单
    destroy:删除订单
    get_status:获取订单状态
    """
    serializer_class = UserOrdersSerializer
    # create_serializer_class = OrdersCreateSerializer
    # update_serializer_class = OrdersUpdateSerializer
    # get_status_serializer_class = OrdersStatusSerializer

    def list(self, request, *args, **kwargs):
        queryset = Orders.objects.filter(uid=request.user.uid,product_type=request.GET.get('product_type'))
        data = []
        for i in queryset:
            dic1 = model_to_dict(i)
            d1 = datetime.datetime.now().replace(tzinfo=datetime.timezone.utc)
            d2 = i.expired_at.replace(tzinfo=datetime.timezone.utc)
            dic1['days_remain']=(d2-d1).days
            data.append(dic1)
        return LimitOffsetResponse(data=data, msg="获取成功")
    
    @action(methods=['get'], detail=False, url_path='order_id', url_name='order_id')
    def retrieve_order(self, request, *args, **kwargs):
        queryset = Orders.objects.filter(id=request.GET.get('id'))
        proxy = ProxyList.objects.filter(order_id=request.GET.get('id'))
        proxy_list = []
        if proxy.exists():
            proxy_data = proxy.all()
            serializer = UserProxyListSerializer(proxy_data, many=True)
            proxy_list = serializer.data
        serializer = self.get_serializer(queryset, many=True)
        return SuccessResponse(data={"order": serializer.data, "proxy_list": proxy_list}, msg="获取成功")
    
    @action(methods=['delete'], detail=True)
    def delete(self, request, *args, **kwargs):
        queryset = Orders.objects.filter(id=request.GET.get('id'), uid = request.user.uid)
        self.perform_destroy(queryset)
        proxylist = ProxyList.objects.filter(order_id=request.GET.get('id'))
        proxylist.delete()
        return SuccessResponse(msg="删除成功")




class EmailView(APIView):
    def post(self, request):
        print("第一次。")
        a = request.data['a']
        b = request.data['b']
        current_time = timezone.now().astimezone(pytz.utc)
        eta_time = current_time + timedelta(seconds=5)
        result = add.apply_async((2,2),eta=eta_time)
        task_id = result.id
        print(result.status)
        print(task_id)
        # 异步调用send_email任务
        # c = add.delay(a, b)
        
        return Response(data={'message': 'success','task_id': task_id})

class VerifyView(APIView):
    def post(self, request):
        print("第二次。")
        task_id = request.data['task_id']
        print(task_id)
        result = AsyncResult(task_id)
        print(result.status)
        print(result.ready())
        # 异步调用send_email任务
        # c = add.delay(a, b)
        
        return Response(data={'message': 'success','result': result.ready()})
