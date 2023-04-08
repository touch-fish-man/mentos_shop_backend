from rest_framework import serializers
from apps.tickets.models import Tickets, Question
from apps.core.viewsets import ComModelViewSet
from apps.tickets.serializers import TicketsSerializer, FQASerializer
from apps.authentication.services import check_chaptcha
from apps.core.json_response import ErrorResponse
from django.conf import settings
# Create your views here.

class TicksApi(ComModelViewSet):
    """
    工单列表
    list:列表
    create:创建
    update:更新
    retrieve:详情
    destroy:删除
    """
    queryset = Tickets.objects.all()
    serializer_class = TicketsSerializer
    search_fields=('username', 'email', 'phone')

    def create(self, request, *args, **kwargs):
        captcha_id = request.data.get('captcha_id')
        if not captcha_id:
            return ErrorResponse(msg='请先获取验证码')
        else:
            request.data.pop('captcha_id')
        captcha_code = request.data.get('captcha')
        if not captcha_code:
            return ErrorResponse(msg='请输入验证码')
        else:
            request.data.pop('captcha')
        if not settings.DEBUG:
            try:
                check_chaptcha(captcha_id, captcha_code)
            except Exception as e:
                return ErrorResponse(msg=e.message)
        return super().create(request, *args, **kwargs)
    
class FQA(ComModelViewSet):
    """
    FAQ
    list:列表
    create:创建
    update:更新
    retrieve:详情
    destroy:删除
    """
    queryset = Question.objects.all()
    serializer_class = FQASerializer
    search_fields=('question', 'answer')
    filterset_fields = ('question', 'answer')