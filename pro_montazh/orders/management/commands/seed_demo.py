"""Создаёт демо-магазин и несколько заявок — чтобы кабинет не был пустым.

Запуск:  python manage.py seed_demo
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from orders.models import Notification, Order

User = get_user_model()

DEMO_LOGIN = 'demo'
DEMO_EMAIL = 'ivan@gmail.com'
DEMO_PASSWORD = 'Montazh2026'


class Command(BaseCommand):
    help = "Создаёт демо-магазин 'Академия дверей' и тестовые заявки"

    def handle(self, *args, **options):
        store, created = User.objects.get_or_create(
            username=DEMO_LOGIN,
            defaults={
                'email': DEMO_EMAIL,
                'role': User.Role.STORE,
                'store_name': 'Академия дверей',
                'manager_full_name': 'Иванович Иван Иванов',
                'phone': '+7 (999) 999-99-99',
                'city': 'г. Москва',
                'street': 'ул. Спиридоновка',
                'house': '25/20с1',
            },
        )
        if created:
            store.set_password(DEMO_PASSWORD)
            store.save()
            self.stdout.write(self.style.SUCCESS(
                f"Создан магазин: логин {DEMO_LOGIN} / пароль {DEMO_PASSWORD}"
            ))
        else:
            self.stdout.write("Демо-магазин уже существует.")

        if store.orders.exists():
            self.stdout.write("Заявки уже созданы — пропускаю.")
            return

        statuses = [
            Order.Status.WAITING_CALL,
            Order.Status.WAITING_SERVICE,
            Order.Status.DONE,
            Order.Status.WAITING_CALL,
            Order.Status.WAITING_SERVICE,
            Order.Status.DONE,
            Order.Status.WAITING_CALL,
            Order.Status.WAITING_SERVICE,
            Order.Status.DONE,
        ]
        today = timezone.localdate()

        for index, status in enumerate(statuses):
            order = Order.objects.create(
                store=store,
                order_type=Order.Type.MONTAZH,
                city=store.city,
                street=store.street,
                house=store.house,
                comment='Изначальный комментарий, который оставил магазин при создании заявки',
                manager_name='Петрова Мария Петровна',
                manager_phone='+7 (999) 999-99-99',
                specialist_name='Петров Павел Петрович',
                specialist_phone='+7 (999) 999-99-99',
                date_from=today,
                date_to=today + timedelta(days=7),
            )
            # Меняем статус через save(), чтобы сработали сигналы
            # и в кабинете появились уведомления, как в макете
            order.status = status
            order.scheduled_date = today + timedelta(days=index)
            order.save()

        Notification.objects.filter(user=store).update(is_read=False)
        self.stdout.write(self.style.SUCCESS(f"Создано заявок: {len(statuses)}"))
