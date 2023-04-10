from rest_framework.decorators import action

from apps.core.json_response import SuccessResponse, ErrorResponse
from apps.core.viewsets import ComModelViewSet
from apps.rewards.models import CouponCode, PointRecord, GiftCard, LevelCode
from apps.rewards.serializers import CouponCodeSerializer, PointRecordSerializer, GiftCardSerializer, LevelCodeSerializer
from apps.core.permissions import IsSuperUser
from apps.core.permissions import IsAuthenticated


class CouponCodeViewSet(ComModelViewSet):
    """
    优惠码
    list:列表
    create:创建
    update:更新
    retrieve:详情
    destroy:删除
    """
    queryset = CouponCode.objects.all()
    serializer_class = CouponCodeSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action == 'list':
            self.permission_classes = []
        return super().get_permissions()

    def list(self, request, *args, **kwargs):
        # 获取当前用户优惠码
        user = request.user
        if user.is_authenticated:
            if user.is_superuser:
                # 管理员获取所有优惠码
                return super().list(request, *args, **kwargs)
            # 普通用户获取自己的优惠码
            request.query_params["limit"] = 100  # 用户获取优惠码时，限制最多100条
            self.queryset = self.queryset.filter(holder_uid=user.id).order_by('-is_used')
            return super().list(request, *args, **kwargs)
        else:
            return ErrorResponse(msg="请先登录")


class PointRecordViewSet(ComModelViewSet):
    """
    积分变动记录
    list:列表
    """
    queryset = PointRecord.objects.all()
    serializer_class = PointRecordSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        # 获取当前用户积分变动记录
        user = request.user
        if user.is_authenticated:
            self.queryset = self.queryset.filter(uid=user.id)
            return super().list(request, *args, **kwargs)
        else:
            return ErrorResponse(msg="请先登录")


class GiftCardViewSet(ComModelViewSet):
    """
    管理员礼品卡列表
    list:列表
    create:创建
    update:更新
    retrieve:详情
    destroy:删除
    base_info:获取礼品卡基本信息
    """
    queryset = GiftCard.objects.all()
    serializer_class = GiftCardSerializer
    search_fields = ['code']
    permission_classes = [IsAuthenticated]

    @action(methods=['get'], detail=False, url_path='base-info', url_name='base-info')
    def base_info(self, request, *args, **kwargs):
        """
        获取礼品卡基本信息
        """
        queryset = self.get_queryset()
        giftcard_amount_list = queryset.values_list('mount', flat=True).distinct()
        # 查询不同金额礼品卡对应的point
        data_list = []
        for mount in giftcard_amount_list:
            giftcard_amount_point_dict = {}
            giftcard_amount_point_dict["mount"] = mount
            giftcard_amount_point_dict["point"] = queryset.filter(mount=mount).first().point
            data_list.append(giftcard_amount_point_dict)
        return SuccessResponse(data=data_list, msg="获取成功")

    @action(methods=['post'], detail=False, url_path='exchange', url_name='exchange')
    def exchange(self, request, *args, **kwargs):
        """
        兑换礼品卡
        """
        exchange_mount = request.data.get("mount")
        user = request.user
        giftcards = GiftCard.objects.filter(mount=exchange_mount, is_used=False).all()
        if giftcards:
            if user.point < giftcards.first().point:
                return ErrorResponse(msg="积分不足")
            giftcard = giftcards.first()
            giftcard.is_exchanged = True
            giftcard.save()
            # 扣除用户积分
            user.point -= giftcard.point
            user.save()
            # 创建积分变动记录
            PointRecord.objects.create(uid=user.id, point=-giftcard.point,
                                       reason=PointRecord.REASON_DICT["exchange"])
            # 给用户增加礼品卡
            CouponCode.objects.create(holder_uid=user.id, code=giftcard.code, discount=giftcard.mount,
                                      is_used=False, code_type=CouponCode.CODE_TYPE_DICT_REVERSE["giftcard"],
                                      holder_username=user.username)
            return SuccessResponse(data=giftcard, msg="兑换成功")
        else:
            return ErrorResponse(msg="礼品卡已兑换完")


class LevelCodeViewSet(ComModelViewSet):
    """
    等级码配置
    list:列表
    put:更新
    """
    permission_classes = [IsSuperUser]
    queryset = LevelCode.objects.all()
    serializer_class = LevelCodeSerializer
