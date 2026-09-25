from django import forms
from django.contrib import admin
from django.utils import timezone
from django.http import FileResponse, HttpResponseForbidden
from django.urls import path, reverse
from django.utils.html import format_html

from .models import Notification, Order, OrderComment, OrderFile, StatusHistory


class OrderFileInline(admin.TabularInline):
    model = OrderFile
    extra = 0
    exclude = ("uploaded_by",)
    readonly_fields = ("uploaded_at", "download_link")

    @admin.display(description="Скачать")
    def download_link(self, obj):
        if not obj.pk:
            return "—"
        url = reverse("admin:app_orderfile_download", args=[obj.pk])
        return format_html('<a href="{}">Скачать файл</a>', url)


class OrderAdminForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = "__all__"

    def clean_status(self):
        status = self.cleaned_data["status"]
        if self.instance.pk and not self.instance.can_transition_to(status):
            raise forms.ValidationError("Переход в этот статус запрещён.")
        return status


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    form = OrderAdminForm
    list_display = (
        "number", "shop_name", "customer_name", "manager", "installer",
        "status", "work_at", "price", "is_urgent", "is_deleted"
    )
    list_filter = ("status", "is_urgent", "is_deleted", "manager", "installer", "work_at")
    search_fields = ("number", "shop_name", "customer_name", "customer_phone")
    readonly_fields = ("number", "created_at", "updated_at")
    inlines = (OrderFileInline,)

    def save_model(self, request, obj, form, change):
        obj._changed_by = request.user
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        obj.is_deleted = True
        obj.deleted_at = timezone.now()
        obj.deleted_by = request.user
        obj.save(update_fields=("is_deleted", "deleted_at", "deleted_by"))

    def delete_queryset(self, request, queryset):
        queryset.update(
            is_deleted=True, deleted_at=timezone.now(), deleted_by=request.user
        )

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, OrderFile) and not instance.uploaded_by_id:
                instance.uploaded_by = request.user
            instance.save()
        for instance in formset.deleted_objects:
            instance.delete()
        formset.save_m2m()


@admin.register(OrderFile)
class OrderFileAdmin(admin.ModelAdmin):
    list_display = ("order", "file", "uploaded_by", "uploaded_at")
    search_fields = ("order__number",)
    readonly_fields = ("uploaded_by", "uploaded_at", "download_link")

    def get_urls(self):
        custom = [
            path("<int:file_id>/download/", self.admin_site.admin_view(self.download), name="app_orderfile_download"),
        ]
        return custom + super().get_urls()

    def download(self, request, file_id):
        obj = self.get_object(request, str(file_id))
        if obj is None or not self.has_view_permission(request, obj):
            return HttpResponseForbidden()
        return FileResponse(obj.file.open("rb"), as_attachment=True)

    @admin.display(description="Скачать")
    def download_link(self, obj):
        if not obj.pk:
            return "—"
        url = reverse("admin:app_orderfile_download", args=[obj.pk])
        return format_html('<a href="{}">Скачать файл</a>', url)

    def save_model(self, request, obj, form, change):
        if not obj.uploaded_by_id:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("message", "manager", "order", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("message", "order__number")
    readonly_fields = ("manager", "order", "message", "created_at")


admin.site.register(OrderComment)
admin.site.register(StatusHistory)
