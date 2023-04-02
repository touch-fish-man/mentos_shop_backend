from rest_framework.decorators import action

from apps.core.json_response import SuccessResponse
from apps.core.viewsets import ComModelViewSet
from apps.rewards.models import CouponCode, PointRecord, GiftCard, LevelCode
from apps.rewards.serializers import CouponCodeSerializer, PointRecordSerializer, GiftCardSerializer,LevelCodeSerializer
from rest_framework.views import APIView


class CouponCodeViewSet(ComModelViewSet):
    """
    优惠码
    """
    queryset = CouponCode.objects.all()
    serializer_class = CouponCodeSerializer
    search_fields = ('code', 'holder_username')
    filter_fields = ('is_used', 'product_id', 'shopify_coupon_id')


class PointRecordViewSet(ComModelViewSet):
    """
    兑换记录
    """
    queryset = PointRecord.objects.all()
    serializer_class = PointRecordSerializer
    search_fields = ('username', 'coupon_code')
    filter_fields = ('product_id', 'shopify_coupon_id')


class GiftCardViewSet(ComModelViewSet):
    """
    管理员礼品卡列表
    """
    queryset = GiftCard.objects.all()
    serializer_class = GiftCardSerializer
    search_fields = ('code')
    @action(methods=['get'], detail=False, url_path='base-info', url_name='base-info')
    def get_giftcard_base_info(self, request, *args, **kwargs):
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

class LevelCodeViewSet(ComModelViewSet):
    """
    等级码
    """
    queryset = LevelCode.objects.all()
    serializer_class = LevelCodeSerializer