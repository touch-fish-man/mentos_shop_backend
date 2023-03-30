
from rest_framework.pagination import LimitOffsetPagination as _LimitOffsetPagination
from apps.core.json_response import LimitOffsetResponse


class CustomLimitOffsetPagination(_LimitOffsetPagination):
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