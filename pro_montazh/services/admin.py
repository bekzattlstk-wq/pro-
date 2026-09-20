from django.contrib import admin

from .models import PriceItem


@admin.register(PriceItem)
class PriceItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'position', 'is_active')
    list_editable = ('price', 'position', 'is_active')
    search_fields = ('title',)
