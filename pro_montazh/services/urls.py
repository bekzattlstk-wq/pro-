from django.urls import path

from .views import notifications_view, price_list_download, price_list_view

urlpatterns = [
    path('price/', price_list_view, name='price_list'),
    path('price/download/', price_list_download, name='price_list_download'),
    path('notifications/', notifications_view, name='notifications'),
]
