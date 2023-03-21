from apps.core.serializers import CommonSerializer
from apps.proxy_server.models import AclList


class AclListSerializer(CommonSerializer):
    class Meta:
        model = AclList
        fields = ('id', 'name', 'description',
                  'acl_value', 'created_at', 'updated_at')
