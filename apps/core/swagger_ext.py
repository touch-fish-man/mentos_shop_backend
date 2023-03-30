from drf_yasg.inspectors import PaginatorInspector
from drf_yasg import openapi
from collections import OrderedDict


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
