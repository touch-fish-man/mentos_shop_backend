import ipaddress

from apps.core.json_response import SuccessResponse, ErrorResponse
from apps.proxy_server.models import Acls, Server, Proxy, AclGroup, ServerGroup, Cidr
from apps.proxy_server.serializers import AclsSerializer, AclsCreateSerializer, AclsUpdateSerializer, \
    ServerSerializer, ServerCreateSerializer, ServerUpdateSerializer, AclGroupSerializer, ServerGroupSerializer, \
    AclGroupCreateSerializer, ServerGroupUpdateSerializer, ServerGroupCreateSerializer, AclGroupUpdateSerializer
from apps.core.validators import CustomUniqueValidator
from apps.core.viewsets import ComModelViewSet
from rest_framework.decorators import action
from apps.core.permissions import IsSuperUser
from apps.core.permissions import IsAuthenticated
from apps.utils.kaxy_handler import KaxyClient
from django.conf import settings
from django.core.cache import cache
from apps.proxy_server.serializers import CidrSerializer,CidrUpdateSerializer
import logging
import json


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
        # acl_str = "\n".join([username + " " + i for i in acl_str_o])
        create_resp = kaxy_client.create_user_acl_by_prefix(username, prefix, acl_value)
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
        if not kaxy_client.status:
            return ErrorResponse(data={"message": "代理服务器连接失败"})
        del_resp = kaxy_client.del_user(username)
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
        if not kaxy_client.status:
            return ErrorResponse(data={"message": "代理服务器连接失败"})
        del_resp = kaxy_client.del_all_user()
        return SuccessResponse(data=del_resp)

    @action(methods=['post'], detail=True, url_path='reset_all_proxy', url_name='reset_proxy')
    def reset_proxy(self, request, *args, **kwargs):
        """
        重置所有用户
        """
        from django_redis import get_redis_connection
        redis_conn = get_redis_connection("default")
        proxy_server = self.get_object()
        server_ip = proxy_server.ip
        # 查询所有用户
        # 更新用户代理
        cidr_whitelist = request.data.get('cidrs', [])
        if len(cidr_whitelist) == 0:
            return ErrorResponse(data={"message": "cidrs不能为空"})
        proxy = Proxy.objects.filter(server_ip=server_ip).all()
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
        request_data = []
        redis_key = "proxy:reset_tasks:{}".format(server_ip)
        tasks_ids = redis_conn.lrange(redis_key, 0, -1)
        if len(tasks_ids):
            from celery.result import AsyncResult
            for tasks_id in tasks_ids:
                task = AsyncResult(tasks_id)
                if task.status not in ["SUCCESS", "FAILURE"]:
                    return ErrorResponse(data={"message": "代理服务器正在重置中，请稍后再试"})
            redis_conn.delete(redis_key)
        tasks_ids_list = []
        for username, order_id in need_reset_user_list.items():
            request_data.append([order_id, username, server_ip])
            from .tasks import reset_proxy_fn
            task_i = reset_proxy_fn.delay(order_id, username, server_ip)
            tasks_ids_list.append(task_i.id)
        if len(tasks_ids_list) > 0:
            redis_conn.rpush(redis_key, *tasks_ids_list)
            redis_conn.expire(redis_key, 60 * 60 * 1)
        return SuccessResponse(data={"message": "reset success", "request_data": request_data})

    @action(methods=['post'], detail=True, url_path='list_acl', url_name='list_acl')
    def list_acl(self, request, *args, **kwargs):
        """
        获取ACL列表
        """
        proxy_server = self.get_object()
        ip = proxy_server.ip
        kaxy_client = KaxyClient(ip)
        try:
            acl_list = kaxy_client.list_acl()
        except Exception as e:
            return ErrorResponse(data={"message": "代理服务器连接失败"})
        return SuccessResponse(data=acl_list)

    @action(methods=['post'], detail=True, url_path='flush_access_log', url_name='flush_access_log')
    def flush_access_log(self, request, *args, **kwargs):
        """
        清理日志
        """
        proxy_server = self.get_object()
        ip = proxy_server.ip
        kaxy_client = KaxyClient(ip)
        clean_resp = kaxy_client.flush_access_log()
        try:
            clean_resp = clean_resp.json()
        except:
            clean_resp = {}
        return SuccessResponse(data=clean_resp)

    @action(methods=['post'], detail=True, url_path='request_api', url_name='request_api')
    def request_api(self, request, *args, **kwargs):
        """
        请求接口
        """
        proxy_server = self.get_object()
        ip = proxy_server.ip
        kaxy_client = KaxyClient(ip)
        json_input = request.data.get('json_input')
        json_input = json.loads(json_input)
        api_ur = request.data.get('uri')
        api = request.data.get('api')
        if not api:
            return ErrorResponse('参数错误')
        try:
            error_msg, api_resp = kaxy_client.request("post", api_ur, json=json_input)
            api_resp = api_resp.json()
        except:
            api_resp = {"message": "请求失败"}
        return SuccessResponse(data=api_resp)


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
    update_serializer_class = AclGroupUpdateSerializer
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


class CidrApi(ComModelViewSet):
    """
    CIDR
    list: CIDR列表
    create: 创建CIDR
    update: 更新CIDR
    retrieve: CIDR详情
    destroy: 删除CIDR
    """
    permission_classes = [IsSuperUser]
    queryset = Cidr.objects.all()
    serializer_class = CidrSerializer
    ordering_fields = ('id', 'cidr', 'created_at')
    search_fields = ('cidr',)  # 搜索字段
    filterset_fields = ['id', 'cidr', 'ip_count']  # 过滤字段
    create_serializer_class = CidrSerializer
    update_serializer_class = CidrUpdateSerializer
