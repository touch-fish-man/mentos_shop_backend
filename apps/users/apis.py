import base64
import datetime
import random
import uuid

from django.contrib.auth.hashers import make_password
from django.core.validators import validate_email
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView

from apps.core.json_response import SuccessResponse, ErrorResponse
from apps.core.viewsets import ComModelViewSet
from apps.users.models import User, Code, InviteLog, RebateRecord
from apps.users.selectors import user_get_login_data
from apps.users.serializers import UserSerializer, UserCreateSerializer, UserUpdateSerializer, BanUserSerializer, \
    InviteLogSerializer, RebateRecordSerializer
from .services import send_email_code, check_email_code, check_verify_id, insert_invite_log
from apps.core.permissions import IsSuperUser
from apps.core.permissions import IsAuthenticated


class UserApi(ComModelViewSet):
    """
    用户接口
    list:列表
    create:新增
    update:修改
    retrieve:查询
    destroy:删除
    user_info:获取用户信息
    change_password:修改密码
    baned_user:禁用用户
    unbaned_user:解禁用户
    """
    serializer_class = UserSerializer
    ordering_fields = ('username', 'email', 'level', 'is_active')
    search_fields = ('username', 'email')  # 搜索字段
    filter_fields = ['uid', 'username', 'email', 'is_superuser', 'level', 'is_active']  # 过滤字段
    queryset = User.objects.all()
    create_serializer_class = UserCreateSerializer
    update_serializer_class = UserUpdateSerializer
    baned_user_serializer_class = BanUserSerializer
    permission_classes = [IsAuthenticated]
    unauthenticated_actions = ['create']

    def get_permissions(self):
        if self.action in ['create']:
            self.permission_classes = []
        return super().get_permissions()

    def create(self, request, *args, **kwargs):

        email_code_id = request.data.get('email_code_id')
        email_code = request.data.get('email_code')
        email = request.data.get('email')
        invite_code = request.data.get('invite_code')
        check_email_code(email, email_code_id, email_code, delete=True)
        resp = super().create(request, *args, **kwargs)
        if invite_code:
            # 插入邀请记录
            if resp.data.get("data", {}).get('id'):
                insert_invite_log(resp.data.get("data", {}).get('id'), invite_code)
        return resp

    @action(methods=['get'], detail=False, url_path='user_info', url_name='user_info')
    def user_info(self, request):
        user = request.user
        data = user_get_login_data(user=user)
        return SuccessResponse(data=data, msg="获取成功")

    @action(methods=['post'], detail=True, url_path='change_password', url_name='change_password')
    def change_password(self, request, *args, **kwargs):

        user = request.user

        if user.is_superuser:
            instance = User.objects.filter(id=kwargs.get("pk")).first()
            password = request.data.get('password')
            instance.password = make_password(password)
            instance.save()
            return SuccessResponse(msg="修改成功")
        else:
            password = request.data.get('password')
            old_password = request.data.get('old_password')
            if user.check_password(old_password):
                user.set_password(password)
                user.save()
                return SuccessResponse(msg="修改成功")
            else:
                return ErrorResponse(msg="密码错误")

    # @action(methods=['post'], detail=False, url_path='reset_password', url_name='reset_password')
    # def reset_password(self, request):
    #     email = request.data.get('email')
    #     password = request.data.get('password')
    #     verify_id = request.data.get('verify_id')
    #     is_success = check_verify_id(email, verify_id)
    #     if not is_success:
    #         return ErrorResponse(msg="验证码错误")
    #     user = User.objects.get(email=email)
    #     user.password = make_password(password)
    #     user.save()
    #     data = user_get_login_data(user=user)
    #     return SuccessResponse(msg="success", data=data)

    @action(methods=['post'], detail=True, url_path='baned_user', url_name='baned_user',
            permission_classes=[IsSuperUser])
    def baned_user(self, request, *args, **kwargs):
        instance = User.objects.filter(id=kwargs.get("pk")).first()
        if instance:
            instance.is_active = False
            instance.save()
            user_data = user_get_login_data(user=instance)
            return SuccessResponse(msg="success", data=user_data)
        else:
            return ErrorResponse(msg="error")

    @action(methods=['post'], detail=True, url_path='unbaned_user', url_name='unbaned_user')
    def unbaned_user(self, request, *args, **kwargs):
        instance = User.objects.filter(id=kwargs.get("pk")).first()
        if instance:
            instance.is_active = True
            instance.save()
            return SuccessResponse(msg="success")
        else:
            return ErrorResponse(msg="error")


class EmailValidateApi(APIView):
    """
    邮箱验证路由
    """

    def post(self, request):
        email = request.data.get('email')
        check_user = request.data.get('check_user')
        req_type = request.data.get('type', 'register')

        try:
            validate_email(email)
        except:
            return ErrorResponse(msg="email error")
        if check_user:
            # 检查用户是否存在,不存在返回错误
            if not User.objects.filter(email=email).exists():
                fake_code_id = random.randint(10, 99)
                msg = "send success"
                data = {"email_code_id": fake_code_id}
                return SuccessResponse(data=data, msg=msg)
        code_id = send_email_code(email, req_type)
        if code_id:
            msg = "send success"
            data = {"email_code_id": code_id}
            return SuccessResponse(data=data, msg=msg)
        else:
            msg = "send fail"
            data = {"email_code_id": ""}
            return ErrorResponse(data=data, msg=msg)


class ResetPasswordApi(APIView):
    """
     忘记密码路由
     post:忘记密码
    """

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        verify_id = request.data.get('verify_id')
        code_obj = Code.objects.filter(verify_id=verify_id, email=email)
        if code_obj.exists():
            db_code = code_obj.first()
            db_code.delete()
        else:
            return ErrorResponse(msg="email error please try again")
        user = User.objects.get(email=email)
        user.password = make_password(password)
        user.save()
        data = user_get_login_data(user=user)
        return SuccessResponse(msg="success", data=data)


class ResetPasswordVerifyApi(APIView):
    """
    忘记密码邮件验证码验证路由
    post:忘记密码邮件验证
    """

    def post(self, request):
        email = request.data.get('email')
        email_code = request.data.get('email_code')
        email_code_id = request.data.get('email_code_id')
        code_obj = check_email_code(email=email, email_code_id=email_code_id, email_code=email_code, delete=False)
        # 验证通过，生成verify_id
        verify_id = str(uuid.uuid4())
        code_obj.verify_id = verify_id
        code_obj.created_at = datetime.datetime.now()
        code_obj.save()

        data = {"verify_id": verify_id}
        return SuccessResponse(data=data, msg="success")


class ChangePasswordApi(APIView):
    """
    用户修改自己密码
    post:修改密码
    """

    def post(self, request):
        user = request.user
        if user.is_authenticated:
            old_password = request.data.get('old_password')
            new_password = request.data.get('new_password')
            if user.check_password(old_password):
                user.password = make_password(new_password)
                user.save()
                return SuccessResponse(msg="修改成功")
            else:
                return ErrorResponse(msg="原密码错误")
        else:
            return ErrorResponse(msg="error")


class InviteLogApi(ListAPIView):
    """
    邀请记录
    get:获取邀请记录
    """
    serializer_class = InviteLogSerializer

    queryset = InviteLog.objects.all()

    def get(self, request, *args, **kwargs):
        # 获取当前用户的邀请记录
        user = request.user
        if user.is_authenticated:
            self.queryset = self.queryset.filter(inviter_user=user)
            return self.list(request, *args, **kwargs)
        else:
            return ErrorResponse(msg="error")


class RebateRecordApi(ListAPIView):
    """
    返利记录
    get:获取返利记录
    """
    serializer_class = RebateRecordSerializer
    queryset = RebateRecord.objects.all()

    def get(self, request, *args, **kwargs):
        # 获取当前用户的返利记录
        user = request.user
        if user.is_authenticated:
            self.queryset = self.queryset.filter(uid=user.id)
            return self.list(request, *args, **kwargs)
        else:
            return ErrorResponse(msg="error")


# class UserLevelRecordApi(ComModelViewSet):
#     """
#     用户等级变更记录
#     """
#     serializer_class = UserLevelRecordSerializer
#     ordering_fields = ('username', 'email', 'level', 'is_active')
#     search_fields = ('username', 'email')  # 搜索字段
#     filter_fields = ['uid', 'username', 'email', 'is_superuser', 'level', 'is_active']  # 过滤字段
#     queryset = UserLevelRecord.objects.all()
#     create_serializer_class = UserLevelRecordSerializer
#     update_serializer_class = UserLevelRecordSerializer
class InviteCodeAPIView(APIView):
    """
    邀请码
    """

    def get(self, request):
        user = request.user
        if user.is_authenticated:
            invite_code = user.invite_code
            data = {"invite_url": "{}/#/createAccount?invite_code={}".format(settings.FRONTEND_URL, invite_code),
                    "invite_code": invite_code}
            return SuccessResponse(data=data)
        else:
            return ErrorResponse(msg="error")
