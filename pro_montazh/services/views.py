import csv

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

from orders.models import Notification

from .models import PriceItem


@login_required
def price_list_view(request):
    """Страница прайс-листа."""
    items = PriceItem.objects.filter(is_active=True)
    return render(request, 'services/price_list.html', {
        'items': items,
        'active_tab': 'price',
    })


@login_required
def price_list_download(request):
    """Выгрузка прайс-листа в CSV (открывается в Excel)."""
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="price-list-pro-montazh.csv"'
    response.write('\ufeff')  # BOM, чтобы Excel не ломал кириллицу

    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Наименование услуги', 'Цена, руб.'])
    for item in PriceItem.objects.filter(is_active=True):
        writer.writerow([item.title, f"{item.price:.2f}".replace('.', ',')])
    return response


@login_required
def notifications_view(request):
    """Уведомления по заявкам текущего магазина."""
    notifications = Notification.objects.filter(user=request.user).select_related('order')
    unread = list(notifications.filter(is_read=False).values_list('id', flat=True))
    context = {
        'notifications': notifications,
        'active_tab': 'notifications',
    }
    response = render(request, 'services/notifications.html', context)
    if unread:
        Notification.objects.filter(id__in=unread).update(is_read=True)
    return response
