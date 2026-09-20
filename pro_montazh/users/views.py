from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from orders.models import Order

from .forms import PasswordChangeSimpleForm, ProfileForm, StoreLoginForm, StoreRegisterForm


def register_view(request):
    if request.user.is_authenticated:
        return redirect('profile')

    if request.method == 'POST':
        form = StoreRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='users.backends.EmailOrUsernameBackend')
            messages.success(request, f"Добро пожаловать! Ваш логин для входа: {user.username}")
            return redirect('profile')
    else:
        form = StoreRegisterForm()
    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('profile')

    if request.method == 'POST':
        form = StoreLoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('profile')
    else:
        form = StoreLoginForm()
    return render(request, 'users/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def profile_view(request):
    """Личный кабинет: данные магазина + последние активные заявки."""
    profile_form = ProfileForm(instance=request.user)
    password_form = PasswordChangeSimpleForm(request.user)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'password':
            password_form = PasswordChangeSimpleForm(request.user, request.POST)
            if password_form.is_valid():
                password_form.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, "Пароль обновлён.")
                return redirect('profile')
            messages.error(request, "Не удалось сменить пароль.")
        else:
            profile_form = ProfileForm(request.POST, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Данные магазина сохранены.")
                return redirect('profile')
            messages.error(request, "Проверьте правильность заполнения полей.")

    active_orders = Order.objects.filter(
        store=request.user, status__in=Order.ACTIVE_STATUSES
    )[:6]

    return render(request, 'users/profile.html', {
        'profile_form': profile_form,
        'password_form': password_form,
        'active_orders': active_orders,
        'active_tab': 'profile',
    })
