from django.urls import path
from apps.site_settings.apis import SiteSettingsApi

urlpatterns = [
    path('sitesettings',SiteSettingsApi.as_view(),name='sitesettings')
]