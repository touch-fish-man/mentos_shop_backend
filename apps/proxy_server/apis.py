from rest_framework.views import APIView,ListAPIView
from apps.core.json_response import JsonResponse




class AclListApi(ListAPIView):
    """
    获取权限列表
    """
    queryset = Acl.objects.all()
    serializer_class = AclSerializer
    serializer_class = AclListApiSerializer
    ordering_fields = ('id', 'uid', 'username', 'email', 'level', 'is_active')
    search_fields = ('username', 'email')  # 搜索字段
    filterset_fields = ['uid', 'username', 'email', 'is_superuser', 'level', 'is_active']  # 过滤字段
    queryset = User.objects.all()

    def get(self, request):
        return JsonResponse(msg="获取成功")
    

