from apps.core.viewsets import ComModelViewSet
from apps.rewards.models import CouponCode, ExchangeRecord
from apps.rewards.serializers import CouponCodeSerializer, ExchangeRecordSerializer

class CouponCodeViewSet(ComModelViewSet):
    """
    优惠码
    """
    queryset = CouponCode.objects.all()
    serializer_class = CouponCodeSerializer
    search_fields = ('code', 'holder_username')
    filter_fields = ('is_used', 'product_id', 'shopify_coupon_id')

class ExchangeRecordViewSet(ComModelViewSet):
    """
    兑换记录
    """
    queryset = ExchangeRecord.objects.all()
    serializer_class = ExchangeRecordSerializer
    search_fields = ('username', 'coupon_code')
    filter_fields = ('product_id', 'shopify_coupon_id')

