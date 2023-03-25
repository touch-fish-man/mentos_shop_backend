from django.urls import path
from .apis import LoginApi,LogoutApi,DiscordOauth2LoginApi,DiscordOauth2RedirectApi,DiscordBindRedirectApi,CaptchaApi,ApiLogin
urlpatterns = [
    path("login", LoginApi.as_view(), name="login"),
    path("logout", LogoutApi.as_view(), name="logout"),
    path("discord/login", DiscordOauth2LoginApi.as_view(), name="discord_login"),
    path("discord/redirect", DiscordOauth2RedirectApi.as_view(), name="discord_redirect"),
    path("discord/bind_redirect", DiscordBindRedirectApi.as_view(), name="discord_bind"),
    path("captcha", CaptchaApi.as_view(), name="captcha"),
    # path("apilogin", ApiLogin.as_view(), name="apilogin"),
]