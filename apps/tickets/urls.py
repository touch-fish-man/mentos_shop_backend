from django.urls import path
from apps.tickets.apis import WorkOrderListApi

urlpatterns = [
    path('workorderlist',WorkOrderListApi.as_view(),name='workorderlist')
]