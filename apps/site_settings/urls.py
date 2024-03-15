from django.urls import path
from apps.site_settings.views import SiteSettingsApi, SocialSettingsApi,ServerLog

urlpatterns = [
    path('config',SiteSettingsApi.as_view(),name='sitesettings'),
    path('social',SocialSettingsApi.as_view(),name='socialsettings'),
    path('logs',ServerLog.as_view(),name='serverlogs'),
]