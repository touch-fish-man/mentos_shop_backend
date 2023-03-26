from rest_framework.decorators import action

from apps.core.json_response import SuccessResponse
from apps.core.viewsets import ComModelViewSet
from apps.orders.models import Orders
from apps.orders.serializers import OrdersSerializer, OrdersCreateSerializer, OrdersUpdateSerializer


class OrdersApi(ComModelViewSet):
    """
    订单接口
    list:获取订单列表
    create:创建订单
    retrieve:获取订单详情
    update:更新订单
    destroy:删除订单
    get_status:获取订单状态
    """
    queryset = Orders.objects.all()
    serializer_class = OrdersSerializer
    create_serializer_class = OrdersCreateSerializer
    update_serializer_class = OrdersUpdateSerializer
    search_fields = ('order_id', 'username', 'uid', 'product_name', 'status')
    filter_fields = ('order_id', 'username', 'uid', 'product_name', 'status')

    @action(methods=['get'], detail=False, url_path='get_status', url_name='get_status')
    def get_status(self, request):
        status = request.data.get('status')
        return SuccessResponse(msg="获取成功", data=status)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, request=request)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return SuccessResponse(data=serializer.data, msg="新增成功")
