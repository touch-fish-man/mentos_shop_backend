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
