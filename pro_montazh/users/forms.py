from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.text import slugify

User = get_user_model()


class StoreRegisterForm(forms.ModelForm):
    """Регистрация магазина. Логином служит email."""

    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(),
        min_length=6,
    )

    class Meta:
        model = User
        fields = ('store_name', 'manager_full_name', 'phone', 'email')

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Пользователь с таким email уже зарегистрирован.")
        return email

    def clean_password(self):
        password = self.cleaned_data.get('password')
        validate_password(password)
        return password

    def _build_username(self, email):
        base = slugify(email.split('@')[0]) or 'store'
        username = base
        counter = 1
        while User.objects.filter(username__iexact=username).exists():
            counter += 1
            username = f"{base}{counter}"
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.username = self._build_username(user.email)
        user.role = User.Role.STORE
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class StoreLoginForm(AuthenticationForm):
    """Вход по логину или email."""

    username = forms.CharField(label="Логин", widget=forms.TextInput())
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput())

    error_messages = {
        'invalid_login': "Неверный логин или пароль.",
        'inactive': "Этот аккаунт отключён.",
    }


class ProfileForm(forms.ModelForm):
    """Редактирование данных магазина в личном кабинете."""

    class Meta:
        model = User
        fields = ('store_name', 'manager_full_name', 'phone', 'email',
                  'city', 'street', 'house')

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Этот email уже занят другим пользователем.")
        return email


class PasswordChangeSimpleForm(forms.Form):
    """Смена пароля из личного кабинета."""

    old_password = forms.CharField(label="Текущий пароль", widget=forms.PasswordInput())
    new_password = forms.CharField(label="Новый пароль", widget=forms.PasswordInput())

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old = self.cleaned_data.get('old_password')
        if not self.user.check_password(old):
            raise ValidationError("Текущий пароль указан неверно.")
        return old

    def clean_new_password(self):
        new = self.cleaned_data.get('new_password')
        validate_password(new, self.user)
        return new

    def save(self):
        self.user.set_password(self.cleaned_data['new_password'])
        self.user.save()
        return self.user
