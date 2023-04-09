from rest_framework.views import APIView
from apps.core.json_response import SuccessResponse, ErrorResponse
from apps.proxy_server.models import Acls, Server, Proxy, AclGroup, ServerGroup
from apps.proxy_server.serializers import AclsSerializer, AclsCreateSerializer, AclsUpdateSerializer, \
    ServerSerializer, ServerCreateSerializer, ServerUpdateSerializer, AclGroupSerializer, ServerGroupSerializer, \
    AclGroupCreateSerializer, ServerGroupUpdateSerializer
from apps.core.validators import CustomUniqueValidator
from apps.core.viewsets import ComModelViewSet
from rest_framework.decorators import action
from apps.core.permissions import IsSuperUser

class AclsApi(ComModelViewSet):
    """
    ACL
    list: ACL列表
    create: 创建ACL
    update: 更新ACL
    retrieve: ACL详情
    destroy: 删除ACL
    """
    permission_classes = [IsSuperUser]
    queryset = Acls.objects.all()
    serializer_class = AclsSerializer
    ordering_fields = ('id', 'name', 'created_at')
    search_fields = ('name', 'description')  # 搜索字段
    filterset_fields = ['id', 'name', 'description', 'acl_value', 'created_at']  # 过滤字段
    create_serializer_class = AclsCreateSerializer
    update_serializer_class = AclsUpdateSerializer


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
    permission_classes = [IsSuperUser]
    queryset = Server.objects.all()
    serializer_class = ServerSerializer
    ordering_fields = ('id', 'name', 'created_at')
    search_fields = ('name', 'description')  # 搜索字段
    filterset_fields = ['id', 'name', 'description', 'created_at']  # 过滤字段
    create_serializer_class = ServerCreateSerializer
    update_serializer_class = ServerUpdateSerializer

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
        proxy_server_info = Acls.objects.filter(proxy_server=proxy_server)
        return SuccessResponse(data=proxy_server_info)

    @action(methods=['get'], detail=True, url_path='get-server-info', url_name='get-server-info')
    def get_server_info(self, request, *args, **kwargs):
        """
        获取代理服务器信息
        """
        proxy_server = self.get_object()
        proxy_server_info = Proxy.objects.filter(proxy_server=proxy_server)
        return SuccessResponse(data=proxy_server_info)


class AclGroupApi(ComModelViewSet):
    """
    ACL组
    list: ACL组列表
    create: 创建ACL组
    update: 更新ACL组
    retrieve: ACL组详情
    destroy: 删除ACL组
    """
    queryset = AclGroup.objects.all()
    serializer_class = AclGroupSerializer
    create_serializer_class = AclGroupCreateSerializer
    update_serializer_class = AclGroupCreateSerializer
    ordering_fields = ('id', 'name', 'created_at')
    search_fields = ('name', 'description')  # 搜索字段
    filterset_fields = ['id', 'name', 'description']  # 过滤字段
    permission_classes = [IsSuperUser]

class ServerGroupApi(ComModelViewSet):
    """
    服务器组
    list: 服务器组列表
    create: 创建服务器组
    update: 更新服务器组
    retrieve: 服务器组详情
    destroy: 删除服务器组
    """
    permission_classes = [IsSuperUser]
    queryset = ServerGroup.objects.all()
    serializer_class = ServerGroupSerializer
    create_serializer_class = ServerGroupSerializer
    update_serializer_class = ServerGroupUpdateSerializer
    ordering_fields = ('id', 'name', 'created_at')
    search_fields = ('name', 'description')  # 搜索字段
    filterset_fields = ['id', 'name', 'description']  # 过滤字段