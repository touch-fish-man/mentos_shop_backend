from django.urls import path
from .apis import  EmailValidateApi, ResetPasswordApi, \
    ChangePasswordApi, ResetPasswordVerifyApi, UserApi,RebateRecordApi,InviteLogApi,InviteCodeAPIView
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'u', UserApi)


urlpatterns = [
    path("email_validate", EmailValidateApi.as_view(), name="email_validate"),
    path("forgot_password", ResetPasswordApi.as_view(), name="reset_password"),
    path("change_password", ChangePasswordApi.as_view(), name="change_password"),
    path("forgot_password_verify", ResetPasswordVerifyApi.as_view(),
         name="reset_password_verify"),
    path("invite_code", InviteCodeAPIView.as_view(), name="invite_code"),
    path("invite_log", InviteLogApi.as_view(), name="invite_log"),
    path("rebate_record", RebateRecordApi.as_view(), name="rebate_record"),

]
urlpatterns += router.urls
