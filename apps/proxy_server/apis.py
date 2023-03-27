from rest_framework.views import APIView
from apps.core.json_response import SuccessResponse, ErrorResponse
from apps.proxy_server.models import AclList, ProxyServer, ProxyList
from apps.proxy_server.serializers import AclListSerializer, AclListCreateSerializer, AclListUpdateSerializer, \
    ProxyServerSerializer, ProxyServerCreateSerializer, ProxyServerUpdateSerializer
from apps.core.validators import CustomUniqueValidator
from apps.core.viewsets import ComModelViewSet
from rest_framework.decorators import action


class AclListApi(ComModelViewSet):
    """
    ACL列表
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
    list: 代理服务器列表
    create: 创建代理服务器
    update: 更新代理服务器
    destroy: 删除代理服务器
    retrieve: 获取代理服务器详情
    change_domain_blacklist: 修改域名黑名单
    list_users: 获取代理服务器用户列表
    get_acl_info: 获取代理服务器ACL信息
    get_server_info: 获取代理服务器信息
    """
    queryset = ProxyServer.objects.all()
    serializer_class = ProxyServerSerializer
    ordering_fields = ('id', 'name', 'created_at')
    search_fields = ('name', 'description')  # 搜索字段
    filterset_fields = ['id', 'name', 'description', 'created_at']  # 过滤字段
    create_serializer_class = ProxyServerCreateSerializer
    update_serializer_class = ProxyServerUpdateSerializer

    @action(methods=['post'], detail=True, url_path='change-domain-blacklist', url_name='change-domain-blacklist')
    def change_domain_blacklist(self, request, *args, **kwargs):
        """
        修改域名黑名单
        """
        proxy_server = self.get_object()
        domain_blacklist = request.data.get('domain_blacklist', '')
        if domain_blacklist:
            proxy_server.domain_blacklist = domain_blacklist
            proxy_server.save()
            return SuccessResponse()
        else:
            return ErrorResponse('参数错误')

    @action(methods=['get'], detail=True, url_path='list-users', url_name='list-users')
    def list_users(self, request, *args, **kwargs):
        """
        获取代理服务器用户列表
        """
        proxy_server = self.get_object()
        users = proxy_server.users.all()
        return SuccessResponse(data=users)

    @action(methods=['get'], detail=True, url_path='get-acl-info', url_name='get-acl-info')
    def get_acl_info(self, request, *args, **kwargs):
        """
        获取代理服务器ACL信息
        """
        proxy_server = self.get_object()
        proxy_server_info = AclList.objects.filter(proxy_server=proxy_server)
        return SuccessResponse(data=proxy_server_info)

    @action(methods=['get'], detail=True, url_path='get-server-info', url_name='get-server-info')
    def get_server_info(self, request, *args, **kwargs):
        """
        获取代理服务器信息
        """
        proxy_server = self.get_object()
        proxy_server_info = ProxyList.objects.filter(proxy_server=proxy_server)
        return SuccessResponse(data=proxy_server_info)
