from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Notification, Order, OrderFile


@receiver(pre_save, sender=Order)
def remember_previous_state(sender, instance, **kwargs):
    """Запоминаем прошлые значения, чтобы поймать изменения."""
    if not instance.pk:
        instance._previous = None
        return
    instance._previous = Order.objects.filter(pk=instance.pk).values(
        'status', 'scheduled_date'
    ).first()


@receiver(post_save, sender=Order)
def notify_order_changes(sender, instance, created, **kwargs):
    """Уведомления магазину: создание заявки, смена статуса, назначение даты."""
    if created:
        Notification.objects.create(
            user=instance.store,
            order=instance,
            text=f"Ваша заявка №{instance.number} взята в обработку",
        )
        return

    previous = getattr(instance, '_previous', None)
    if not previous:
        return

    if previous['status'] != instance.status:
        Notification.objects.create(
            user=instance.store,
            order=instance,
            text=f'Статус заявки №{instance.number} изменен на "{instance.get_status_display()}"',
        )

    if previous['scheduled_date'] != instance.scheduled_date and instance.scheduled_date:
        Notification.objects.create(
            user=instance.store,
            order=instance,
            text=(
                f"По вашей заявке №{instance.number} назначена дата монтажа: "
                f"{instance.scheduled_date.strftime('%d.%m.%Y')}"
            ),
        )


@receiver(post_save, sender=OrderFile)
def notify_new_file(sender, instance, created, **kwargs):
    """Магазин получает уведомление, когда менеджер прикрепил файл."""
    if created and instance.uploaded_by_role == OrderFile.Role.MANAGER:
        Notification.objects.create(
            user=instance.order.store,
            order=instance.order,
            text=f"К заявке №{instance.order.number} добавлен новый файл: {instance.display_name}",
        )
