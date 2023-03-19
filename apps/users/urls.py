from django.urls import path
from .apis import UserListApi, UserInfoApi, UserRegisterApi, CaptchaApi, EmailValidateApi, ResetPasswordApi, \
    ChangePasswordApi

urlpatterns = [
    path("register", UserRegisterApi.as_view(), name="register"),
    path("captcha", CaptchaApi.as_view(), name="captcha"),
    path("email_validate", EmailValidateApi.as_view(), name="email_validate"),
    path("info", UserInfoApi.as_view(), name="info"),
    path("reset_password", ResetPasswordApi.as_view(), name="reset_password"),
    path("change_password", ChangePasswordApi.as_view(), name="change_password"),
    path("", UserListApi.as_view(), name="list"),

]
