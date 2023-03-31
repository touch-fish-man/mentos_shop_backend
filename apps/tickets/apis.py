from rest_framework import serializers
from apps.tickets.models import Tickets
from apps.core.viewsets import ComModelViewSet
from apps.tickets.serializers import TicketsSerializer
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
        captcha_code = request.data.get('captcha')
        if not settings.DEBUG:
            try:
                check_chaptcha(captcha_id, captcha_code)
            except Exception as e:
                return ErrorResponse(msg=e.message)
        return super().create(request, *args, **kwargs)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
