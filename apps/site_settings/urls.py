from django.urls import path
from apps.site_settings.apis import SiteSettingsApi, SocialSettingsApi

urlpatterns = [
    path('config',SiteSettingsApi.as_view(),name='sitesettings'),
    path('social',SocialSettingsApi.as_view(),name='socialsettings')
]