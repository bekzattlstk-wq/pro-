from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AdminDashboardView, AdminOrderViewSet, ChangePasswordView, EmployeeListView,
    LogoutView, MeView, NotificationViewSet, OrderFileViewSet, OrderViewSet,
)

router = DefaultRouter()
router.register("orders", OrderViewSet, basename="order")
router.register("order-files", OrderFileViewSet, basename="order-file")
router.register("notifications", NotificationViewSet, basename="notification")

admin_router = DefaultRouter()
admin_router.register("orders", AdminOrderViewSet, basename="admin-order")

urlpatterns = [
    path("me/", MeView.as_view(), name="me"),
    path("me/password/", ChangePasswordView.as_view(), name="change-password"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("admin/dashboard/", AdminDashboardView.as_view(), name="admin-dashboard"),
    path("admin/employees/", EmployeeListView.as_view(), name="admin-employees"),
    path("admin/", include(admin_router.urls)),
    path("", include(router.urls)),
]
