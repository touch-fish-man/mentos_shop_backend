from django.urls import path
from .apis import UserListApi, UserInfoApi, UserRegisterApi,CaptchaApi,EmailValidateApi

urlpatterns = [
    path("register", UserRegisterApi.as_view(), name="register"),
    path("captcha", CaptchaApi.as_view(), name="captcha"),
    path("email_validate", EmailValidateApi.as_view(), name="email_validate"),
    path("info", UserInfoApi.as_view(), name="info"),
    path("", UserListApi.as_view(), name="list"),

]