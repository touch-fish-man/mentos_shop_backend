from collections import OrderedDict

from rest_framework.pagination import LimitOffsetPagination as _LimitOffsetPagination
from rest_framework.response import Response
from apps.core.json_response import SuccessResponse,LimitOffsetResponse
from drf_yasg.inspectors import PaginatorInspector
from drf_yasg import openapi
from collections import OrderedDict


class LimitOffsetPagination(_LimitOffsetPagination):
    """
    重写LimitOffsetPagination类,修改返回数据格式
    """
    default_limit = 10
    max_limit = 50
    limit_query_description = "每页数量"
    offset_query_description = "偏移量"

    def get_paginated_response(self, data):
        """
        We redefine this method in order to return `limit` and `offset`.
        This is used by the frontend to construct the pagination itself.
        """
        return LimitOffsetResponse(data=data, offset=self.offset, limit=self.limit, total=self.count)

class LimitOffsetPaginationInspector(PaginatorInspector):
    """
    重写sawgger LimitOffsetPaginationInspector类,修改返回数据格式
    """
    def get_paginated_response(self, paginator, response_schema):
        return openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties=OrderedDict([
                    ('code', openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码')),
                    ('msg', openapi.Schema(type=openapi.TYPE_STRING, description='提示信息')),
                    ('data', openapi.Schema(type=openapi.TYPE_OBJECT, properties=OrderedDict([
                        ('offset', openapi.Schema(type=openapi.TYPE_INTEGER, description='偏移量')),
                        ('limit', openapi.Schema(type=openapi.TYPE_INTEGER, description='每页数量')),
                        ('total', openapi.Schema(type=openapi.TYPE_INTEGER, description='总数')),
                        ('data', response_schema),
                    ]))),
                ])
            )
