from django.contrib.auth import get_user_model, logout
from django.db.models import Count, Q
from django.http import FileResponse
from django.utils import timezone
from rest_framework import filters, generics, permissions, status, viewsets
from rest_framework.permissions import IsAdminUser
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.authtoken.views import ObtainAuthToken

from .models import Notification, Order, OrderFile
from .permissions import IsStaffOrReadOnly
from .serializers import (
    AdminOrderSerializer, CommentSerializer, EmployeeSerializer, EmptySerializer,
    HistorySerializer, ManagerSerializer, NotificationSerializer,
    OrderFileSerializer, OrderSerializer, PasswordSerializer,
)

User = get_user_model()


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = (IsStaffOrReadOnly,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ("number", "customer_name", "customer_phone", "shop_name")
    ordering_fields = ("created_at", "work_at", "price")
    queryset = Order.objects.filter(is_deleted=False).select_related(
        "created_by", "manager", "installer"
    ).prefetch_related("files")

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(created_by=self.request.user) |
                Q(manager=self.request.user) |
                Q(installer=self.request.user)
            ).distinct()
        requested_status = self.request.query_params.get("status")
        if requested_status:
            queryset = queryset.filter(status=requested_status)
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.instance._changed_by = self.request.user
        serializer.save()


class OrderFileViewSet(viewsets.ModelViewSet):
    serializer_class = OrderFileSerializer
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser)
    queryset = OrderFile.objects.select_related("order", "order__manager")
    http_method_names = ("get", "post", "delete", "head", "options")

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_staff:
            return queryset.filter(order__is_deleted=False)
        return queryset.filter(
            Q(order__created_by=self.request.user) |
            Q(order__manager=self.request.user) |
            Q(order__installer=self.request.user),
            order__is_deleted=False,
        ).distinct()

    def perform_create(self, serializer):
        order = serializer.validated_data["order"]
        allowed = self.request.user.is_staff or order.created_by_id == self.request.user.id
        if not allowed:
            raise PermissionDenied("Нет прав на добавление файла к этой заявке.")
        source = OrderFile.Source.ADMIN if self.request.user.is_staff else OrderFile.Source.SHOP
        serializer.save(uploaded_by=self.request.user, source=source)

    def perform_destroy(self, instance):
        if not self.request.user.is_staff and instance.uploaded_by_id != self.request.user.id:
            raise PermissionDenied("Нет прав на удаление этого файла.")
        instance.file.delete(save=False)
        instance.delete()

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        order_file = self.get_object()
        return FileResponse(order_file.file.open("rb"), as_attachment=True)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Notification.objects.select_related("order")

    def get_queryset(self):
        return super().get_queryset().filter(manager=self.request.user)

    @action(detail=True, methods=["post"], url_path="mark-read")
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response(self.get_serializer(notification).data)

    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request):
        updated = self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({"updated": updated})


class MeView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ManagerSerializer

    def get(self, request):
        return Response(ManagerSerializer(request.user).data)

    def patch(self, request):
        serializer = ManagerSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ChangePasswordView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = PasswordSerializer

    def post(self, request):
        serializer = PasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        if not request.user.check_password(serializer.validated_data["old_password"]):
            raise ValidationError({"old_password": "Неверный пароль."})
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password"])
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class LogoutView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = EmptySerializer

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class LoginView(ObtainAuthToken):
    throttle_classes = (AnonRateThrottle,)


class AdminOrderViewSet(viewsets.ModelViewSet):
    serializer_class = AdminOrderSerializer
    permission_classes = (IsAdminUser,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ("number", "shop_name", "customer_name", "customer_phone")
    ordering_fields = ("created_at", "work_at", "price")
    queryset = Order.objects.filter(is_deleted=False).select_related("manager", "installer").prefetch_related(
        "files", "comments"
    )

    def get_queryset(self):
        queryset = super().get_queryset()
        order_status = self.request.query_params.get("status")
        return queryset.filter(status=order_status) if order_status else queryset

    def perform_update(self, serializer):
        serializer.instance._changed_by = self.request.user
        serializer.save()

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.deleted_by = self.request.user
        instance.save(update_fields=("is_deleted", "deleted_at", "deleted_by"))

    @action(detail=True, methods=["post"])
    def comment(self, request, pk=None):
        serializer = CommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = self.get_object()
        serializer.save(order=order, author=request.user)
        if order.manager:
            Notification.objects.create(
                manager=order.manager, order=order,
                message=f"Добавлен комментарий к заявке №{order.number}",
            )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        history = self.get_object().status_history.all()
        return Response(HistorySerializer(history, many=True).data)


class EmployeeListView(generics.ListAPIView):
    serializer_class = EmployeeSerializer
    permission_classes = (IsAdminUser,)

    def get_queryset(self):
        group = {"manager": "Managers", "installer": "Installers"}.get(
            self.request.query_params.get("role")
        )
        if not group:
            return User.objects.none()
        return User.objects.filter(groups__name=group, is_active=True)


class AdminDashboardView(generics.GenericAPIView):
    permission_classes = (IsAdminUser,)
    serializer_class = AdminOrderSerializer

    def get(self, request):
        queryset = Order.objects.filter(is_deleted=False)
        counts = dict(queryset.values_list("status").annotate(total=Count("id")))
        orders = queryset.select_related("manager", "installer")[:6]
        notifications = Notification.objects.filter(manager=request.user)[:6]
        return Response({
            "counts": counts,
            "orders": AdminOrderSerializer(orders, many=True).data,
            "unread_notifications": Notification.objects.filter(
                manager=request.user, is_read=False
            ).count(),
            "notifications": NotificationSerializer(notifications, many=True).data,
        })
