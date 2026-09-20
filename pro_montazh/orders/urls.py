from django.urls import path

from .views import (
    order_create_view,
    order_detail_view,
    order_files_download,
    order_list_view,
    order_search_view,
)

urlpatterns = [
    path('', order_list_view, name='order_list'),
    path('create/', order_create_view, name='order_create'),
    path('search/', order_search_view, name='order_search'),
    path('<str:number>/', order_detail_view, name='order_detail'),
    path('<str:number>/files/<str:side>/', order_files_download, name='order_files_download'),
]
