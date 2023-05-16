import logging
import traceback

from django.conf import settings
from django.db.models import ProtectedError
from django.http import Http404
from rest_framework.exceptions import APIException as DRFAPIException, AuthenticationFailed,NotAuthenticated
from rest_framework.views import set_rollback

from .json_response import ErrorResponse
from django.core.exceptions import ValidationError
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
    traceback.print_exc()

    if isinstance(ex, AuthenticationFailed):
        code = 401
        msg = ex.detail
    elif isinstance(ex,Http404):
        code = 400
        msg = "not found"
    elif isinstance(ex,NotAuthenticated):
        code = 4001
        msg = "not authenticated"
    elif isinstance(ex, DRFAPIException):
        set_rollback()
        logger.error(traceback.format_exc())
        msg = 'Server error, please contact the administrator'
    elif isinstance(ex, ProtectedError):
        set_rollback()
        msg = "The current data is in use and cannot be deleted"
    elif isinstance(ex, ValidationError):
        set_rollback()
        msg = ex.message
    elif isinstance(ex, Exception):
        logger.error(traceback.format_exc())
        if settings.DEBUG:
            msg = str(traceback.format_exc())
        else:
            msg = 'Server error, please contact the administrator'
    else:
        logger.error(traceback.format_exc())
        msg = 'Server error, please contact the administrator'

    return ErrorResponse(msg=msg, code=code)
