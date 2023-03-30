from django.urls import path
from .apis import  EmailValidateApi, ResetPasswordApi, \
    ChangePasswordApi, ResetPasswordVerifyApi, UserApi,RebateRecordApi,InviteLogApi,InviteCodeAPIView
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'', UserApi)
router.register(r'rebate_record', RebateRecordApi)
router.register(r'invite_log', InviteLogApi)


urlpatterns = [
    path("email_validate", EmailValidateApi.as_view(), name="email_validate"),
    # path("info", UserInfoApi.as_view(), name="info"),
    path("forgot_password", ResetPasswordApi.as_view(), name="reset_password"),
    path("change_password", ChangePasswordApi.as_view(), name="change_password"),
    path("forgot_password_verify", ResetPasswordVerifyApi.as_view(),
         name="reset_password_verify"),
    path("invite_code", InviteCodeAPIView.as_view(), name="invite_code"),
    # path("", UserListApi.as_view(), name="list"),

]
urlpatterns += router.urls
