from django.urls import include, path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)
urlpatterns = [
    # path("auth/", include(("apps.authentication.urls", "authentication"))),
    # path("users/", include(("apps.users.urls", "users"))),
    # path("errors/", include(("apps.errors.urls", "errors"))),
    # 获取Token的接口
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    # 刷新Token有效期的接口
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # 验证Token的有效性
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    path('auth/', include('rest_framework.urls', namespace='rest_framework')),
    
    
    ]