from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Notification, Order, OrderFile, StatusHistory

User = get_user_model()


@receiver(pre_save, sender=Order)
def remember_order_changes(sender, instance, **kwargs):
    instance._previous_order = None
    if instance.pk:
        instance._previous_order = sender.objects.filter(pk=instance.pk).values(
            "status", "manager_id"
        ).first()


@receiver(post_save, sender=Order)
def notify_order_changes(sender, instance, created, **kwargs):
    if created and not instance.number:
        instance.number = f"АД{instance.pk:08d}"
        sender.objects.filter(pk=instance.pk).update(number=instance.number)
    previous = getattr(instance, "_previous_order", None)
    if created:
        admins = User.objects.filter(is_staff=True, is_active=True)
        Notification.objects.bulk_create([
            Notification(
                manager=admin, order=instance,
                message=f"Поступила новая заявка №{instance.number}",
            )
            for admin in admins
        ])
        if instance.manager and not admins.filter(pk=instance.manager_id).exists():
            Notification.objects.create(
                manager=instance.manager, order=instance,
                message=f"Вам назначена заявка №{instance.number}",
            )
        return

    if previous and previous["manager_id"] != instance.manager_id and instance.manager:
        Notification.objects.create(
            manager=instance.manager, order=instance,
            message=f"Вам назначена заявка №{instance.number}",
        )

    if previous and previous["status"] != instance.status:
        StatusHistory.objects.create(
            order=instance,
            old_status=previous["status"],
            new_status=instance.status,
            changed_by=getattr(instance, "_changed_by", None),
        )
        if instance.manager:
            Notification.objects.create(
                manager=instance.manager, order=instance,
                message=f"Статус заявки №{instance.number}: {instance.get_status_display()}",
            )


@receiver(post_save, sender=OrderFile)
def notify_file_added(sender, instance, created, **kwargs):
    if created and instance.order.manager:
        Notification.objects.create(
            manager=instance.order.manager,
            order=instance.order,
            message=f"Добавлен файл к заявке №{instance.order.number}",
        )
