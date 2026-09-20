from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import Notification, Order, OrderFile

User = get_user_model()


class OrderTests(TestCase):
    def setUp(self):
        self.store = User.objects.create_user(
            username='demo', email='demo@mail.ru', password='Montazh2026',
            store_name='Академия дверей', city='г. Москва',
        )
        self.other = User.objects.create_user(
            username='other', email='other@mail.ru', password='Montazh2026',
            store_name='Другие двери',
        )
        self.client.login(username='demo', password='Montazh2026')

    def test_number_generation(self):
        first = Order.objects.create(store=self.store)
        second = Order.objects.create(store=self.store)
        self.assertTrue(first.number.startswith('АД'))
        self.assertEqual(int(second.number[2:]), int(first.number[2:]) + 1)

    def test_create_order_view(self):
        response = self.client.post(reverse('order_create'), {
            'order_type': Order.Type.MONTAZH,
            'city': 'г. Москва',
            'street': 'ул. Спиридоновка',
            'house': '25/20с1',
            'comment': 'Монтаж 4 дверей',
            'date_from': '2026-01-15',
            'date_to': '2026-01-22',
        })
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertRedirects(response, reverse('order_detail', args=[order.number]))

    def test_create_order_rejects_wrong_dates(self):
        response = self.client.post(reverse('order_create'), {
            'order_type': Order.Type.MONTAZH,
            'city': 'г. Москва', 'street': 'ул. Ленина', 'house': '1',
            'date_from': '2026-01-22', 'date_to': '2026-01-15',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.count(), 0)

    def test_cannot_open_foreign_order(self):
        foreign = Order.objects.create(store=self.other)
        response = self.client.get(reverse('order_detail', args=[foreign.number]))
        self.assertEqual(response.status_code, 404)

    def test_notifications_created_on_status_change(self):
        order = Order.objects.create(store=self.store)
        self.assertEqual(Notification.objects.filter(order=order).count(), 1)
        order.status = Order.Status.DONE
        order.save()
        self.assertEqual(Notification.objects.filter(order=order).count(), 2)

    def test_file_upload_and_zip_download(self):
        order = Order.objects.create(store=self.store)
        upload = SimpleUploadedFile('Замеры.txt', b'test content')
        self.client.post(reverse('order_detail', args=[order.number]), {'files': upload})
        self.assertEqual(order.files.count(), 1)
        self.assertEqual(order.files.first().uploaded_by_role, OrderFile.Role.STORE)

        response = self.client.get(reverse('order_files_download', args=[order.number, 'store']))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/zip')

    def test_search(self):
        order = Order.objects.create(store=self.store)
        response = self.client.get(reverse('order_search'), {'q': order.number})
        self.assertContains(response, order.number)

    def test_order_list_shows_only_active_by_default(self):
        active = Order.objects.create(store=self.store)
        done = Order.objects.create(store=self.store)
        Order.objects.filter(pk=done.pk).update(status=Order.Status.DONE)
        response = self.client.get(reverse('order_list'))
        self.assertContains(response, active.number)
        self.assertNotContains(response, done.number)
