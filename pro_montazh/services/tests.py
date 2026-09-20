from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import PriceItem

User = get_user_model()


class ServicesTests(TestCase):
    def setUp(self):
        User.objects.create_user(username='demo', email='d@m.ru', password='Montazh2026')
        self.client.login(username='demo', password='Montazh2026')

    def test_price_list_filled_by_migration(self):
        self.assertGreater(PriceItem.objects.count(), 10)

    def test_price_page(self):
        response = self.client.get(reverse('price_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Установка двери МДФ')

    def test_price_download_csv(self):
        response = self.client.get(reverse('price_list_download'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment', response['Content-Disposition'])

    def test_notifications_page(self):
        response = self.client.get(reverse('notifications'))
        self.assertEqual(response.status_code, 200)
