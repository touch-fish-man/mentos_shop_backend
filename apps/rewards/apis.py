from rest_framework.decorators import action

from apps.core.json_response import SuccessResponse
from apps.core.viewsets import ComModelViewSet
from apps.rewards.models import CouponCode, PointRecord, GiftCard
from apps.rewards.serializers import CouponCodeSerializer, PointRecordSerializer, GiftCardSerializer
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
    search_fields = ('code', 'username')
    filter_fields = ('is_used', 'product_id', 'shopify_coupon_id')
    @action(methods=['get'], detail=False, url_path='base-info', url_name='base-info')
    def get_giftcard_base_info(self, request, *args, **kwargs):
        """
        获取礼品卡基本信息
        """
        queryset = self.get_queryset()
        giftcard_amount_list = queryset.values_list('amount', flat=True).distinct()
        # 查询不同金额礼品卡对应的point
        giftcard_amount_point_dict = {}
        for amount in giftcard_amount_list:
            giftcard_amount_point_dict[amount] = queryset.filter(amount=amount).first().point
        return SuccessResponse(data=giftcard_amount_point_dict)

