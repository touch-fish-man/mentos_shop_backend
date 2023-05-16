import logging
import traceback

from django.conf import settings
from django.db.models import ProtectedError
from django.http import Http404
from rest_framework.exceptions import APIException as DRFAPIException, AuthenticationFailed,NotAuthenticated
from rest_framework.views import set_rollback

from .json_response import ErrorResponse

logger = logging.getLogger(__name__)


def CustomExceptionHandler(ex, context):
    """
    统一异常拦截处理
    目的:(1)取消所有的500异常响应,统一响应为标准错误返回
        (2)准确显示错误信息
    :param ex:
    :param context:
    :return:
    """
    msg = ''
    code = 4000
    if settings.DEBUG:
        traceback.print_exc()

        if isinstance(ex, AuthenticationFailed):
            code = 401
            msg = ex.detail
        elif isinstance(ex,Http404):
            code = 400
            msg = "接口地址不正确"
        elif isinstance(ex,NotAuthenticated):
            code = 4001
            msg = "未登录"
        elif isinstance(ex, DRFAPIException):
            set_rollback()
            print(ex.detail)
            msg = ex.detail
            if isinstance(msg,dict):
                for k, v in msg.items():
                    for i in v:
                        msg = "%s:%s" % (k, i)
        elif isinstance(ex, ProtectedError):
            set_rollback()
            msg = "删除失败:该条数据与其他数据有相关绑定"
        # elif isinstance(ex, DatabaseError):
        #     set_rollback()
        #     msg = "接口服务器异常,请联系管理员"
        elif isinstance(ex, Exception):
            logger.error(traceback.format_exc())

            msg = str(traceback.format_exc())
    else:
        if isinstance(ex, NotAuthenticated):
            code = 4001
            msg = str(ex.detail)
        else:
            logger.error(traceback.format_exc())
            msg = 'Server error, please contact the administrator'

    return ErrorResponse(msg=msg, code=code)
