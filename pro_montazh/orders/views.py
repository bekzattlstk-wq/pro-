import io
import zipfile

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import OrderCreateForm
from .models import Order, OrderFile

MAX_UPLOAD_SIZE = 20 * 1024 * 1024  # 20 МБ на файл


def _store_orders(user):
    """Заявки только текущего магазина (чужие видеть нельзя)."""
    return Order.objects.filter(store=user)


def _save_files(request, order, files):
    """Сохраняет загруженные магазином файлы с проверкой размера."""
    saved = 0
    for uploaded in files:
        if uploaded.size > MAX_UPLOAD_SIZE:
            messages.error(request, f"Файл «{uploaded.name}» больше 20 МБ и не был загружен.")
            continue
        OrderFile.objects.create(
            order=order,
            file=uploaded,
            original_name=uploaded.name,
            uploaded_by=request.user,
            uploaded_by_role=OrderFile.Role.STORE,
        )
        saved += 1
    return saved


@login_required
def order_list_view(request):
    """Список активных заявок магазина."""
    show_all = request.GET.get('all') == '1'
    orders = _store_orders(request.user)
    if not show_all:
        orders = orders.filter(status__in=Order.ACTIVE_STATUSES)
    return render(request, 'orders/order_list.html', {
        'orders': orders,
        'show_all': show_all,
        'active_tab': 'orders',
    })


@login_required
def order_detail_view(request, number):
    """Карточка заявки + загрузка файлов магазином."""
    order = get_object_or_404(_store_orders(request.user), number=number)

    if request.method == 'POST':
        files = request.FILES.getlist('files')
        if not files:
            messages.error(request, "Выберите хотя бы один файл.")
        else:
            saved = _save_files(request, order, files)
            if saved:
                messages.success(request, f"Загружено файлов: {saved}.")
        return redirect('order_detail', number=order.number)

    return render(request, 'orders/order_detail.html', {
        'order': order,
        'manager_files': order.files_by_manager(),
        'store_files': order.files_by_store(),
        'active_tab': 'orders',
    })


@login_required
def order_create_view(request):
    """Создание новой заявки."""
    if request.method == 'POST':
        form = OrderCreateForm(request.POST, store=request.user)
        if form.is_valid():
            order = form.save(commit=False)
            order.store = request.user
            order.save()
            _save_files(request, order, request.FILES.getlist('files'))
            messages.success(request, f"Заявка {order.number} создана.")
            return redirect('order_detail', number=order.number)
        messages.error(request, "Проверьте правильность заполнения полей.")
    else:
        form = OrderCreateForm(store=request.user)

    return render(request, 'orders/order_create.html', {
        'form': form,
        'active_tab': 'create',
    })


@login_required
def order_search_view(request):
    """Поиск заявки по номеру, типу или адресу."""
    query = (request.GET.get('q') or '').strip()
    orders = []
    if query:
        orders = _store_orders(request.user).filter(number__icontains=query)
        if not orders.exists():
            orders = _store_orders(request.user).filter(comment__icontains=query)
    return render(request, 'orders/order_search.html', {
        'orders': orders,
        'query': query,
        'active_tab': 'search',
    })


@login_required
def order_files_download(request, number, side):
    """Скачивание всех файлов заявки одним архивом."""
    order = get_object_or_404(_store_orders(request.user), number=number)
    if side == 'manager':
        files = order.files_by_manager()
    elif side == 'store':
        files = order.files_by_store()
    else:
        raise Http404

    if not files.exists():
        messages.error(request, "К заявке пока не прикреплены файлы.")
        return redirect('order_detail', number=order.number)

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
        used = set()
        for item in files:
            name = item.display_name
            counter = 1
            while name in used:
                counter += 1
                name = f"{counter}_{item.display_name}"
            used.add(name)
            try:
                with item.file.open('rb') as handle:
                    archive.writestr(name, handle.read())
            except (FileNotFoundError, ValueError):
                continue

    buffer.seek(0)
    response = HttpResponse(buffer.read(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{order.number}-{side}.zip"'
    return response
