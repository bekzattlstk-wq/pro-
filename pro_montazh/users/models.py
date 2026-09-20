from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Пользователь системы. Роль STORE — магазин (пользовательская часть),
    ADMIN — сотрудник сервиса (админская часть)."""

    class Role(models.TextChoices):
        STORE = 'STORE', 'Магазин (Клиент)'
        ADMIN = 'ADMIN', 'Администратор'

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.STORE,
        verbose_name="Роль",
    )
    email = models.EmailField(unique=True, verbose_name="Email")
    store_name = models.CharField(max_length=255, blank=True, verbose_name="Название магазина")
    manager_full_name = models.CharField(max_length=255, blank=True, verbose_name="ФИО менеджера")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Контактный телефон")

    # Адрес магазина
    city = models.CharField(max_length=100, blank=True, default="г. Москва", verbose_name="Город")
    street = models.CharField(max_length=255, blank=True, verbose_name="Улица")
    house = models.CharField(max_length=50, blank=True, verbose_name="Дом")

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.store_name or self.username

    @property
    def is_store(self):
        return self.role == self.Role.STORE

    @property
    def display_name(self):
        return self.store_name or self.manager_full_name or self.username

    @property
    def avatar_letter(self):
        """Первая буква названия магазина для круглой аватарки."""
        name = (self.store_name or self.username).strip()
        return name[0].upper() if name else "?"

    @property
    def order_prefix(self):
        """Префикс номера заявки: 'Академия дверей' -> 'АД'."""
        words = [w for w in (self.store_name or "").split() if w]
        if len(words) >= 2:
            return (words[0][0] + words[1][0]).upper()
        if len(words) == 1:
            return words[0][:2].upper()
        return (self.username[:2] or "ЗК").upper()

    @property
    def full_address(self):
        parts = [p for p in (self.city, self.street, self.house) if p]
        return ", ".join(parts)
