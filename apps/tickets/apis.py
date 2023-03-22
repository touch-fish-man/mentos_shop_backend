from django.shortcuts import render
import pytz
from datetime import datetime, timedelta

from captcha.views import CaptchaStore
from django.core.validators import validate_email
from rest_framework import serializers
from rest_framework.generics import ListAPIView

from apps.tickets.selectors import workorder_list
from apps.api.pagination import LimitOffsetPagination, get_paginated_response
from apps.core.json_response import SuccessResponse, ErrorResponse
from apps.tickets.models import WorkOrder
# Create your views here.

class WorkOrderListApi(ListAPIView):
    """
    工单列表路由
    """
    def post(self,request):
        username = request.data.get('username')
        phone = request.data.get('phone')
        email = request.data.get('email')
        message = request.data.get('message')
        captcha_id = request.data.get('captcha_id')
        captcha_code = request.data.get('captcha')
        try:
            validate_email(email)
        except:
            return ErrorResponse(msg="邮箱格式错误")
        if captcha_id is None:
            return ErrorResponse(msg="验证码错误")
        if captcha_code is None:
            return ErrorResponse(msg="验证码错误")
        expiration = CaptchaStore.objects.filter(id=captcha_id).first().expiration
        expiration = expiration.astimezone(pytz.timezone("Asia/Shanghai"))
        response = CaptchaStore.objects.filter(id=captcha_id).first().response
        image_code = CaptchaStore.objects.filter(id=captcha_id).first()
        five_minute_ago = datetime.now() - timedelta(hours=0, minutes=5, seconds=0)
        five_minute_ago = five_minute_ago.replace(tzinfo=pytz.timezone("Asia/Shanghai"))
        if image_code and five_minute_ago > expiration:
            image_code.delete()
            return ErrorResponse(msg="验证码过期")
        else:
            if image_code and response.lower() == captcha_code.lower():
                image_code.delete()
            else:
                image_code.delete()
                return ErrorResponse(msg="验证码错误")
        workorder = WorkOrder.objects.create(username=username, phone=phone,
                                        email=email, message=message)
        workorder.save()
        return  SuccessResponse("发送成功")


    class Pagination(LimitOffsetPagination):
        default_limit = 5

    class FilterSerializer(serializers.Serializer):
        username = serializers.CharField(required=False,allow_null=True)
        phone = serializers.CharField(required=False, allow_null=True)
        email = serializers.EmailField(required=False,allow_null=True)
        
    
    class OutputSerializer(serializers.ModelSerializer):
        class Meta:
            model = WorkOrder
            fields = ("username", "phone", "email","message")

    def get(self,request):
        filters_serializer = self.FilterSerializer(data=request.query_params)
        filters_serializer.is_valid(raise_exception=True)

        workorders = workorder_list(filters=filters_serializer.validated_data)

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.OutputSerializer,
            queryset=workorders,
            request=request,
            view=self,
        )
    
    def delete(self,request):
        username = request.data.get('username')
        phone = request.data.get('phone')
        email = request.data.get('email')
        message = request.data.get('message')
        workorder = WorkOrder.objects.filter(username=username,phone=phone,email=email,message=message)
        workorder.delete()
        return SuccessResponse(msg="删除成功")