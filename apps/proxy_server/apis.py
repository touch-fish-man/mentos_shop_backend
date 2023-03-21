from rest_framework.views import APIView, ListAPIView
from apps.core.json_response import JsonResponse, ErrorResponse
from apps.proxy_server.models import AclList, ProxyServer, ProxyList
from apps.proxy_server.serializers import AclListSerializer, AclListCreateSerializer, AclListUpdateSerializer
from apps.core.validators import CustomUniqueValidator
from rest_framework.viewsets import ModelViewSet
from apps.core.viewsets import ComModelViewSet


class AclListApi(ComModelViewSet):
    """
    获取权限列表
    """
    queryset = AclList.objects.all()
    serializer_class = AclListSerializer
    ordering_fields = ('id', 'name', 'created_at')
    search_fields = ('name', 'description')  # 搜索字段
    filterset_fields = ['id', 'name', 'description', 'acl_value', 'created_at']  # 过滤字段
    create_serializer_class = AclListCreateSerializer
    update_serializer_class = AclListUpdateSerializer

    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
class ProxyServerApi(ComModelViewSet):
    """
    代理服务器
    """
    queryset = ProxyServer.objects.all()
    serializer_class = ProxyServerSerializer
    ordering_fields = ('id', 'name', 'created_at')
    search_fields = ('name', 'description')  # 搜索字段
    filterset_fields = ['id', 'name', 'description', 'created_at']  # 过滤字段
    create_serializer_class = ProxyServerCreateSerializer
    update_serializer_class = ProxyServerUpdateSerializer

    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
