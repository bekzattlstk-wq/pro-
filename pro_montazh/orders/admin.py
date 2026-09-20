from django.contrib import admin

from .models import Notification, Order, OrderFile


class OrderFileInline(admin.TabularInline):
    model = OrderFile
    extra = 0
    fields = ('file', 'uploaded_by_role', 'uploaded_at')
    readonly_fields = ('uploaded_at',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('number', 'store', 'order_type', 'status', 'created_at', 'scheduled_date')
    list_filter = ('status', 'order_type', 'created_at')
    search_fields = ('number', 'store__store_name', 'comment')
    date_hierarchy = 'created_at'
    inlines = (OrderFileInline,)


@admin.register(OrderFile)
class OrderFileAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'order', 'uploaded_by_role', 'uploaded_at')
    list_filter = ('uploaded_by_role',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('text', 'user', 'order', 'is_read', 'created_at')
    list_filter = ('is_read',)
