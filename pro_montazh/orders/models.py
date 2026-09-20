import os

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Order(models.Model):
    """Заявка магазина на услугу сервиса."""

    class Type(models.TextChoices):
        MONTAZH = 'MONTAZH', 'Монтаж'
        ZAMER = 'ZAMER', 'Замер'
        REMONT = 'REMONT', 'Ремонт / доработка'
        DEMONTAZH = 'DEMONTAZH', 'Демонтаж'

    class Status(models.TextChoices):
        WAITING_CALL = 'WAITING_CALL', 'Ожидает звонок'
        WAITING_SERVICE = 'WAITING_SERVICE', 'Ожидает услугу'
        IN_PROGRESS = 'IN_PROGRESS', 'В работе'
        DONE = 'DONE', 'Завершен'
        CANCELED = 'CANCELED', 'Отменен'

    # Статусы, которые считаются «активными» (заявка ещё в работе)
    ACTIVE_STATUSES = (Status.WAITING_CALL, Status.WAITING_SERVICE, Status.IN_PROGRESS)

    number = models.CharField(max_length=32, unique=True, editable=False, verbose_name="Номер заявки")
    store = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name="Магазин",
    )
    order_type = models.CharField(
        max_length=20, choices=Type.choices, default=Type.MONTAZH, verbose_name="Тип заявки"
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.WAITING_CALL, verbose_name="Статус заявки"
    )

    # Адрес объекта
    city = models.CharField(max_length=100, blank=True, verbose_name="Город")
    street = models.CharField(max_length=255, blank=True, verbose_name="Улица")
    house = models.CharField(max_length=50, blank=True, verbose_name="Дом")

    comment = models.TextField(blank=True, verbose_name="Комментарий магазина")
    manager_comment = models.TextField(blank=True, verbose_name="Комментарий менеджера")

    # Заполняет админская часть
    manager_name = models.CharField(max_length=255, blank=True, verbose_name="Менеджер")
    manager_phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон менеджера")
    specialist_name = models.CharField(max_length=255, blank=True, verbose_name="Специалист по монтажу")
    specialist_phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон специалиста")

    date_from = models.DateField(null=True, blank=True, verbose_name="Желаемая дата (с)")
    date_to = models.DateField(null=True, blank=True, verbose_name="Желаемая дата (по)")
    scheduled_date = models.DateField(null=True, blank=True, verbose_name="Дата назначения работ")

    created_at = models.DateTimeField(default=timezone.now, verbose_name="Дата заявки")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлена")

    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"
        ordering = ('-created_at', '-id')

    def __str__(self):
        return f"{self.number} — {self.get_order_type_display()}"

    def get_absolute_url(self):
        return reverse('order_detail', args=[self.number])

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = self._generate_number()
        if not self.city and self.store_id:
            self.city = self.store.city
        super().save(*args, **kwargs)

    def _generate_number(self):
        """Формат номера: АД00521250 (префикс магазина + сквозной счётчик)."""
        prefix = self.store.order_prefix if self.store_id else 'ЗК'
        last = (
            Order.objects.filter(number__startswith=prefix)
            .order_by('-number')
            .values_list('number', flat=True)
            .first()
        )
        start = 521250
        if last:
            digits = ''.join(ch for ch in last[len(prefix):] if ch.isdigit())
            if digits:
                start = int(digits) + 1
        return f"{prefix}{start:08d}"

    @property
    def is_active(self):
        return self.status in self.ACTIVE_STATUSES

    @property
    def status_color(self):
        """CSS-класс цвета статуса для шаблонов."""
        return {
            self.Status.DONE: 'text-emerald-600',
            self.Status.CANCELED: 'text-gray-400',
        }.get(self.status, 'text-emerald-500')

    @property
    def address(self):
        return ", ".join(p for p in (self.city, self.street, self.house) if p)

    def files_by_manager(self):
        return self.files.filter(uploaded_by_role=OrderFile.Role.MANAGER)

    def files_by_store(self):
        return self.files.filter(uploaded_by_role=OrderFile.Role.STORE)


def order_file_path(instance, filename):
    return f"order_files/{instance.order.number}/{filename}"


class OrderFile(models.Model):
    """Файл, прикреплённый к заявке магазином или менеджером сервиса."""

    class Role(models.TextChoices):
        STORE = 'STORE', 'Магазин'
        MANAGER = 'MANAGER', 'Менеджер'

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='files', verbose_name="Заявка")
    file = models.FileField(upload_to=order_file_path, verbose_name="Файл")
    original_name = models.CharField(max_length=255, blank=True, verbose_name="Имя файла")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='uploaded_files',
        verbose_name="Кто загрузил",
    )
    uploaded_by_role = models.CharField(
        max_length=10, choices=Role.choices, default=Role.STORE, verbose_name="Сторона"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")

    class Meta:
        verbose_name = "Файл заявки"
        verbose_name_plural = "Файлы заявок"
        ordering = ('uploaded_at', 'id')

    def __str__(self):
        return self.display_name

    def save(self, *args, **kwargs):
        if not self.original_name and self.file:
            self.original_name = os.path.basename(self.file.name)
        super().save(*args, **kwargs)

    @property
    def display_name(self):
        return self.original_name or os.path.basename(self.file.name)


class Notification(models.Model):
    """Уведомление магазина по заявке."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name="Получатель",
    )
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='notifications',
        null=True, blank=True, verbose_name="Заявка",
    )
    text = models.CharField(max_length=500, verbose_name="Текст уведомления")
    is_read = models.BooleanField(default=False, verbose_name="Прочитано")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        ordering = ('-created_at', '-id')

    def __str__(self):
        return self.text
