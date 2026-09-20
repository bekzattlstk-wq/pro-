from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'store_name', 'manager_full_name', 'email', 'phone', 'role')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('username', 'store_name', 'manager_full_name', 'email', 'phone')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Данные магазина', {
            'fields': ('role', 'store_name', 'manager_full_name', 'phone', 'city', 'street', 'house'),
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Данные магазина', {
            'fields': ('email', 'role', 'store_name', 'manager_full_name', 'phone'),
        }),
    )
