from rest_framework.viewsets import ModelViewSet
from .json_response import SuccessResponse, LimitOffsetResponse, ErrorResponse

class CustomModelViewSet(ModelViewSet):
    values_queryset = None
    ordering_fields = '__all__'
    create_serializer_class = None
    update_serializer_class = None
    filter_fields = '__all__'
    search_fields = ()
    # extra_filter_backends = [DataLevelPermissionsFilter]
    # permission_classes = [CustomPermission]
    import_field_dict = {}
    export_field_label = {}

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, request=request)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return SuccessResponse(data=serializer.data, msg="新增成功")
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True, request=request)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True, request=request)
        return LimitOffsetResponse(data=serializer.data, msg="获取成功")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return SuccessResponse(data=serializer.data, msg="获取成功")

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial, request=request)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return SuccessResponse(data=serializer.data, msg="修改成功")
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return SuccessResponse(msg="删除成功")