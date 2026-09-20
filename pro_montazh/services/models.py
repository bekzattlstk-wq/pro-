from django.db import models


class PriceItem(models.Model):
    """Позиция прайс-листа сервиса."""

    title = models.CharField(max_length=255, verbose_name="Наименование услуги")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена, руб.")
    position = models.PositiveIntegerField(default=0, verbose_name="Порядок")
    is_active = models.BooleanField(default=True, verbose_name="Показывать в прайсе")

    class Meta:
        verbose_name = "Услуга (прайс-лист)"
        verbose_name_plural = "Прайс-лист"
        ordering = ('position', 'id')

    def __str__(self):
        return f"{self.title} — {self.price}"
