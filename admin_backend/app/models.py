from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Order(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Новая"
        WAITING_CALL = "waiting_call", "Ожидает звонок"
        WAITING_SERVICE = "waiting_service", "Ожидает услугу"
        IN_PROGRESS = "in_progress", "В работе"
        PAUSED = "paused", "Приостановлен"
        COMPLETED = "completed", "Завершён"
        CANCELLED = "cancelled", "Отменён"

    number = models.CharField(max_length=30, unique=True,null=True,
                              blank=True, editable=False)

    shop_name = models.CharField(max_length=200)

    service_name = models.CharField(max_length=200)

    customer_name = models.CharField(max_length=200)

    customer_phone = models.CharField(max_length=30)

    city = models.CharField(max_length=100, blank=True)

    street = models.CharField(max_length=150, blank=True)

    house = models.CharField(max_length=50, blank=True)

    customer_comment = models.TextField(blank=True)

    admin_comment = models.TextField(blank=True)

    price = models.DecimalField(max_digits=12, decimal_places=2,
        default=0, validators=[MinValueValidator(0)])

    status = models.CharField(max_length=30,choices=Status.choices,
        default=Status.NEW,db_index=True)

    manager = models.ForeignKey(settings.AUTH_USER_MODEL,null=True,
        blank=True,on_delete=models.PROTECT,related_name="managed_orders")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.PROTECT, related_name="created_orders"
    )

    installer = models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,
        on_delete=models.PROTECT,related_name="installation_orders")

    work_at = models.DateTimeField(null=True, blank=True)

    # Временно сохраняется для совместимости со старыми данными.
    planned_date = models.DateField(null=True, blank=True)

    is_urgent = models.BooleanField(default=False)

    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="deleted_orders"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def can_transition_to(self, status):
        if status == self.status:
            return True
        transitions = {
            self.Status.NEW: {self.Status.WAITING_CALL, self.Status.CANCELLED},
            self.Status.WAITING_CALL: {self.Status.WAITING_SERVICE, self.Status.PAUSED, self.Status.CANCELLED},
            self.Status.WAITING_SERVICE: {self.Status.IN_PROGRESS, self.Status.PAUSED, self.Status.CANCELLED},
            self.Status.IN_PROGRESS: {self.Status.COMPLETED, self.Status.PAUSED},
            self.Status.PAUSED: {self.Status.WAITING_CALL, self.Status.WAITING_SERVICE, self.Status.CANCELLED},
        }
        return status in transitions.get(self.status, set())

    def __str__(self):
        return self.number or f"Заявка {self.pk}"


class OrderFile(models.Model):
    class Source(models.TextChoices):
        SHOP = "shop", "Магазин"
        ADMIN = "admin", "Администратор"
        MANAGER = "manager", "Менеджер"
        INSTALLER = "installer", "Монтажник"

    source = models.CharField(max_length=20,choices=Source.choices,default=Source.ADMIN)

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="files")
    file = models.FileField(upload_to="order_files/%Y/%m/")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    uploaded_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.file.name


class Notification(models.Model):
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="notifications")
    message = models.CharField(max_length=300)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.message

class OrderComment(models.Model):

    order = models.ForeignKey(Order,on_delete=models.CASCADE,related_name="comments")

    author = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)

    text = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.order} - {self.author}"

class StatusHistory(models.Model):
    order = models.ForeignKey(Order,on_delete=models.CASCADE,related_name="status_history")

    old_status = models.CharField(max_length=30)

    new_status = models.CharField(max_length=30)

    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
