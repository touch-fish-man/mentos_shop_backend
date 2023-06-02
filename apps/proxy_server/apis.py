import ipaddress

from rest_framework.views import APIView
from apps.core.json_response import SuccessResponse, ErrorResponse
from apps.proxy_server.models import Acls, Server, Proxy, AclGroup, ServerGroup
from apps.proxy_server.serializers import AclsSerializer, AclsCreateSerializer, AclsUpdateSerializer, \
    ServerSerializer, ServerCreateSerializer, ServerUpdateSerializer, AclGroupSerializer, ServerGroupSerializer, \
    AclGroupCreateSerializer, ServerGroupUpdateSerializer,ServerGroupCreateSerializer
from apps.core.validators import CustomUniqueValidator
from apps.core.viewsets import ComModelViewSet
from rest_framework.decorators import action
from apps.core.permissions import IsSuperUser
from apps.core.permissions import IsAuthenticated
from apps.utils.kaxy_handler import KaxyClient
from apps.orders.services import create_proxy_by_order,create_proxy_by_id
from apps.proxy_server.tasks import create_proxy_task
from django.conf import settings
import logging

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
    get_server_info: 获取代理服务器信息
    create_user_by_prefix: 通过前缀创建用户
    delete_user: 删除用户
    delete_all_user: 删除所有用户
    reset_proxy: 重置所有用户
    """
    permission_classes = [IsSuperUser]
    queryset = Server.objects.all()
    serializer_class = ServerSerializer
    ordering_fields = ('id', 'name', 'created_at')
    search_fields = ('name', 'description')  # 搜索字段
    filterset_fields = ['id', 'name', 'description', 'created_at']  # 过滤字段
    create_serializer_class = ServerCreateSerializer
    update_serializer_class = ServerUpdateSerializer

    @action(methods=['get'], detail=True, url_path='get_server_info', url_name='get_server_info')
    def get_server_info(self, request, *args, **kwargs):
        """
        获取代理服务器信息
        """
        proxy_server = self.get_object()
        ip = proxy_server.ip
        # url = "http://{}:65533".format(ip)
        kaxy = KaxyClient(ip)
        server_info = kaxy.get_server_info()
        user_list = kaxy.list_users()
        try:
            server_info = server_info.json()
        except:
            server_info = {}
        try:
            user_list = user_list.json()
        except:
            user_list = {}
        return SuccessResponse(data={"server_info": server_info, "user_list": user_list})

    @action(methods=['post'], detail=True, url_path='create_user_by_prefix', url_name='create_user_by_prefix')
    def create_user_by_prefix(self, request, *args, **kwargs):
        """
        通过前缀创建用户
        """
        if settings.DEBUG:
            return SuccessResponse(data={"code": 200, "message": "success"})
        proxy_server = self.get_object()
        ip = proxy_server.ip
        prefix = request.data.get('prefix')
        username = request.data.get('username')
        acl_group = request.data.get('acl_group')
        if not prefix:
            return ErrorResponse('参数错误')
        if not acl_group:
            return ErrorResponse('参数错误')
        acl_value = AclGroup.objects.get(id=acl_group).acl_value
        kaxy_client = KaxyClient(ip)
        acl_str_o = acl_value.split('\n')
        # acl_str = "\n".join([username + " " + i for i in acl_str_o])
        create_resp = kaxy_client.create_user_acl_by_prefix(username, prefix, acl_str_o)
        return SuccessResponse(data=create_resp)

    @action(methods=['post'], detail=True, url_path='delete_user', url_name='delete_user')
    def delete_user(self, request, *args, **kwargs):
        """
        删除用户
        """
        if settings.DEBUG:
            return SuccessResponse(data={"code": 200, "message": "success"})
        proxy_server = self.get_object()
        ip = proxy_server.ip
        username = request.data.get('username')
        if not username:
            return ErrorResponse('参数错误')
        kaxy_client = KaxyClient(ip)
        del_resp = kaxy_client.del_user(username)
        try:
            del_resp = del_resp.json()
        except:
            del_resp = {}
        return SuccessResponse(data=del_resp)

    @action(methods=['post'], detail=True, url_path='delete_all_user', url_name='delete_all_user')
    def delete_all_user(self, request, *args, **kwargs):
        """
        删除所有用户
        """
        if settings.DEBUG:
            return SuccessResponse(data={"code": 200, "message": "success"})
        proxy_server = self.get_object()
        ip = proxy_server.ip
        kaxy_client = KaxyClient(ip)
        del_resp = kaxy_client.del_all_user()
        try:
            del_resp = del_resp.json()
        except:
            del_resp = {}
        return SuccessResponse(data=del_resp)
    @action(methods=['post'], detail=True, url_path='reset_all_proxy', url_name='reset_proxy')
    def reset_proxy(self, request, *args, **kwargs):
        """
        重置所有用户
        """
        proxy_server = self.get_object()
        server_ip = proxy_server.ip
        # 查询所有用户
        # 更新用户代理
        cidr_whitelist = request.data.get('cidrs', [])
        if len(cidr_whitelist) == 0:
            return ErrorResponse('参数错误')
        proxy=Proxy.objects.filter(server_ip=server_ip).all()
        need_reset_user_list = {}
        need_delete_proxy_list = []
        for p in proxy:
            is_in = False
            for cidr in cidr_whitelist:
                # 判断ip是否在白名单内
                if ipaddress.ip_address(p.ip) in ipaddress.ip_network(cidr):
                    is_in = True
                    break
            if not is_in:
                need_delete_proxy_list.append(p.id)
                need_reset_user_list[p.username] = p.order_id
        logging.info("need_reset_user_list:{}".format(need_reset_user_list))
        request_data=[]
        for username, order_id in need_reset_user_list.items():
            request_data.append([order_id,username, server_ip])
            create_proxy_task(order_id,username, server_ip)
        return SuccessResponse(data={"message": "reset success","request_data":request_data})


class AclGroupApi(ComModelViewSet):
    """
    ACL组
    list: ACL组列表
    create: 创建ACL组
    update: 更新ACL组
    retrieve: ACL组详情
    destroy: 删除ACL组
    """
    queryset = AclGroup.objects.filter(soft_delete=False).all()
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
    create_serializer_class = ServerGroupCreateSerializer
    update_serializer_class = ServerGroupUpdateSerializer
    ordering_fields = ('id', 'name', 'created_at')
    search_fields = ('name', 'description')  # 搜索字段
    filterset_fields = ['id', 'name', 'description']  # 过滤字段
