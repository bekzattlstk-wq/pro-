from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Notification,Order,OrderComment,OrderFile,StatusHistory


User = get_user_model()


class ManagerSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name", "email")
        read_only_fields = ("id", "username")


class PasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        validate_password(value, self.context["request"].user)
        return value


class EmptySerializer(serializers.Serializer):
    pass


class OrderFileSerializer(serializers.ModelSerializer):
    file_name = serializers.CharField(source="file.name", read_only=True)

    class Meta:
        model = OrderFile
        fields = ("id", "order", "file", "file_name", "source", "uploaded_at")
        read_only_fields = ("id", "file_name", "uploaded_at")
        extra_kwargs = {"file": {"write_only": True}}


class OrderSerializer(serializers.ModelSerializer):
    files = OrderFileSerializer(many=True, read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Order
        fields = (
            "id", "number", "shop_name", "service_name", "customer_name",
            "customer_phone", "city", "street", "house", "customer_comment",
            "price", "status", "status_label", "created_by", "manager",
            "installer", "work_at", "is_urgent", "files", "created_at", "updated_at",
        )
        read_only_fields = (
            "id", "number", "created_by", "manager", "installer", "status",
            "status_label", "is_urgent", "files", "created_at", "updated_at",
        )

    def validate_manager(self, value):
        if not value.is_active:
            raise serializers.ValidationError("Менеджер должен быть активным.")
        return value


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ("id", "order", "message", "is_read", "created_at")
        read_only_fields = ("id", "order", "message", "created_at")


class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.get_full_name", read_only=True)

    class Meta:
        model = OrderComment
        fields = ("id", "author", "author_name", "text", "created_at")
        read_only_fields = ("id", "author", "author_name", "created_at")


class EmployeeSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "full_name", "email")


class HistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = StatusHistory
        fields = ("id", "old_status", "new_status", "changed_by", "created_at")


class AdminOrderSerializer(serializers.ModelSerializer):
    files = OrderFileSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Order
        fields = (
            "id", "number", "shop_name", "service_name", "customer_name",
            "customer_phone", "city", "street", "house", "customer_comment",
            "admin_comment", "price", "status", "status_label", "created_by", "manager",
            "installer", "work_at", "is_urgent", "files", "comments",
            "is_deleted", "created_at", "updated_at",
        )
        read_only_fields = (
            "id", "number", "created_by", "status_label", "files", "comments", "is_deleted",
            "created_at", "updated_at",
        )

    def validate_manager(self, value):
        if value and not value.groups.filter(name="Managers").exists():
            raise serializers.ValidationError("Этот пользователь не является менеджером.")
        return value

    def validate_installer(self, value):
        if value and not value.groups.filter(name="Installers").exists():
            raise serializers.ValidationError("Этот пользователь не является монтажником.")
        return value

    def validate_status(self, value):
        if self.instance and not self.instance.can_transition_to(value):
            raise serializers.ValidationError("Переход в этот статус запрещён.")
        return value
