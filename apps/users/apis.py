import base64
import datetime
import uuid

from captcha.views import CaptchaStore, captcha_image
from django.contrib.auth.hashers import make_password
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.validators import validate_email
from rest_framework.decorators import action
from rest_framework.views import APIView

from apps.core.json_response import SuccessResponse, ErrorResponse
from apps.core.viewsets import ComModelViewSet
from apps.users.models import User, Code
from apps.users.selectors import user_get_login_data
from apps.users.serializers import UserSerializer, UserCreateSerializer, UserUpdateSerializer, BanUserSerializer
from .services import send_email_code, check_email_code, check_verify_id


class UserInfoApi(LoginRequiredMixin, APIView):
    """
    用户信息路由
    """

    def get(self, request):
        user = request.user
        print(user)
        data = user_get_login_data(user=user)
        return SuccessResponse(data=data, msg="获取成功")

    def post(self, request):
        user = request.user
        email = request.data.get('email')
        user.email = email
        user.save()
        return SuccessResponse(msg="修改成功")

    def delete(self, request):
        user = request.user
        user.delete()
        return SuccessResponse(msg="删除成功")

    def put(self, request):
        user = request.user
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')
        user.username = username
        user.password = make_password(password)
        user.email = email
        user.save()
        return SuccessResponse(msg="修改成功")


class UserApi(ComModelViewSet):
    """
    用户路由
    """
    serializer_class = UserSerializer
    ordering_fields = ('username', 'email', 'level', 'is_active')
    search_fields = ('username', 'email')  # 搜索字段
    filter_fields = ['uid', 'username', 'email', 'is_superuser', 'level', 'is_active']  # 过滤字段
    queryset = User.objects.all()
    create_serializer_class = UserCreateSerializer
    update_serializer_class = UserUpdateSerializer
    reset_password_serializer_class = UserSerializer
    baned_user_serializer_class = BanUserSerializer

    @action(methods=['get'], detail=False, url_path='user_info', url_name='user_info')
    def user_info(self, request):
        user = request.user
        data = user_get_login_data(user=user)
        return SuccessResponse(data=data, msg="获取成功")

    @action(methods=['post'], detail=True, url_path='change_password', url_name='change_password')
    def change_password(self, request, *args, **kwargs):
        user = request.user
        if user.is_superuser:
            instance = User.objects.filter(uid=kwargs.get("pk")).first()
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

    @action(methods=['post'], detail=False, url_path='reset_password', url_name='reset_password')
    def reset_password(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        verify_id = request.data.get('verify_id')
        is_success = check_verify_id(email, verify_id)
        if not is_success:
            return ErrorResponse(msg="验证码错误")
        user = User.objects.get(email=email)
        user.password = make_password(password)
        user.save()
        data = user_get_login_data(user=user)
        return SuccessResponse(msg="success", data=data)

    @action(methods=['post'], detail=True, url_path='baned_user', url_name='baned_user')
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

        try:
            validate_email(email)
        except:
            return ErrorResponse(msg="email error")
        if check_user:
            # 检查用户是否存在,不存在返回错误
            if not User.objects.filter(email=email).exists():
                return ErrorResponse(msg="email not exist")
        code_id = send_email_code(email)
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
    重置密码路由
    """

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        verify_id = request.data.get('verify_id')
        code_obj = Code.objects.filter(verify_id=verify_id, email=email)
        if code_obj.exists():
            db_code = code_obj.order_by('-create_time').first()
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
    重置密码验证路由
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
    修改密码路由
    """

    def post(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        if user.check_password(old_password):
            user.password = make_password(new_password)
            user.save()
            return SuccessResponse(msg="修改成功")
        else:
            return ErrorResponse(msg="原密码错误")
