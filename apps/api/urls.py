from django.urls import include, path

urlpatterns = [
    path("auth/", include("apps.authentication.urls")),
    path("users/", include("apps.users.urls")),
    path("tickets/", include("apps.tickets.urls")),
    path("servers/", include("apps.proxy_server.urls")),
    # path("errors/", include("apps.errors.urls")),
    # 获取Token的接口
    ]