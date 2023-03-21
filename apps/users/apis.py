import base64
import time
import uuid

from captcha.views import CaptchaStore, captcha_image
from django.contrib.auth.hashers import make_password
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.validators import validate_email
from rest_framework import serializers
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action

from apps.core.json_response import SuccessResponse, ErrorResponse, LimitOffsetResponse
from apps.users.models import User, Code
from apps.users.selectors import user_get_login_data
from apps.users.serializers import UserSerializer, UserListSerializer
from .services import send_email_code
from apps.core.viewsets import CustomModelViewSet


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


class UserApi(CustomModelViewSet):
    """
    用户路由
    """
    serializer_class = UserListSerializer
    ordering_fields = ('id', 'uid', 'username', 'email', 'level', 'is_active')
    search_fields = ('username', 'email')  # 搜索字段
    filterset_fields = ['uid', 'username', 'email',
                        'is_superuser', 'level', 'is_active']  # 过滤字段
    queryset = User.objects.all()
    create_serializer_class = UserSerializer
    update_serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        # # 管理员权限
        # if request.user.is_superuser:
        #     return super().destroy(request, *args, **kwargs)
        # else:
        #     return ErrorResponse(msg="没有权限")
        return super().destroy(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @action(methods=['get'], detail=False, url_path='user_info', url_name='user_info')
    def user_info(self, request):
        user = request.user
        data = user_get_login_data(user=user)
        return SuccessResponse(data=data, msg="获取成功")

    @action(methods=['post'], detail=False, url_path='change_password', url_name='change_password')
    def change_password(self, request):
        user = request.user
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

    @action(methods=['post'], detail=False, url_path='baned_user', url_name='baned_user')
    def baned_user(self, request, *args, **kwargs):
        instance = Users.objects.filter(id=kwargs.get("pk")).first()
        if instance:
            instance.is_active = False
            instance.save()
            return SuccessResponse(msg="success")
        else:
            return ErrorResponse(msg="error")
    
    @action(methods=['post'], detail=False, url_path='unbaned_user', url_name='unbaned_user')
    def unbaned_user(self, request, *args, **kwargs):
        instance = Users.objects.filter(id=kwargs.get("pk")).first()
        if instance:
            instance.is_active = True
            instance.save()
            return SuccessResponse(msg="success")
        else:
            return ErrorResponse(msg="error")


class UserRegisterApi(APIView):
    """
    用户注册路由
    """

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')
        invite_code = request.data.get('invite_code')
        email_code = request.data.get('email_code')
        email_code_id = request.data.get('email_code_id')
        code_item = Code.objects.filter(id=email_code_id, email=email_code)
        if code_item.exists():
            db_code = code_item.order_by('-create_at').first()
        else:
            return Response({'status': False, 'msg': 'email error'}, status=200)
        time_now = int(time.time())
        del_time = time_now - db_code.create_at
        if del_time >= 600:
            db_code = Code.objects.filter(email=email)
            db_code.delete()
            return Response({'status': False, 'msg': 'code overdue'}, status=200)
        if email_code != db_code.code:
            return Response({'status': False, 'msg': 'code fail'}, status=200)
        user = User.objects.create_user(username=username, password=password,
                                        email=email, invite_code=invite_code)
        user.save()
        db_code = Code.objects.filter(email=email)
        db_code.delete()
        return SuccessResponse(msg="注册成功")


class CaptchaApi(APIView):
    """
    验证码路由
    """

    def get(self, request):
        data = {}
        hashkey = CaptchaStore.generate_key()
        id = CaptchaStore.objects.filter(hashkey=hashkey).first().id
        imgage = captcha_image(request, hashkey)
        # 将图片转换为base64
        image_base = base64.b64encode(imgage.content)
        data = {
            "captcha_id": id,
            "captcha_image_base": "data:image/png;base64," + image_base.decode("utf-8"),
        }
        return SuccessResponse(data=data, msg="获取成功")


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
        code_obj = Code.objects.filter(email=email, id=email_code_id)
        if code_obj.exists():
            db_code = code_obj.order_by('-create_time').first()
        else:
            return ErrorResponse(msg="email error please try again")
        time_now = int(time.time())
        del_time = time_now - db_code.create_time
        if del_time >= 600:
            db_code = Code.objects.filter(email=email)
            db_code.delete()
            return ErrorResponse(msg="code expired please try again")
        if email_code != db_code.code:
            return ErrorResponse(msg="code error please try again")
        # 验证通过，生成verify_id
        verify_id = str(uuid.uuid4())
        db_code.verify_id = verify_id
        db_code.save()
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
