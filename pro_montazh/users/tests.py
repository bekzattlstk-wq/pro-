from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class AuthFlowTests(TestCase):
    def test_register_creates_store_and_logs_in(self):
        response = self.client.post(reverse('register'), {
            'store_name': 'Академия дверей',
            'manager_full_name': 'Иванович Иван Иванов',
            'phone': '+7 (999) 999-99-99',
            'email': 'ivan@gmail.com',
            'password': 'Montazh2026',
        })
        self.assertRedirects(response, reverse('profile'))
        user = User.objects.get(email='ivan@gmail.com')
        self.assertEqual(user.role, User.Role.STORE)
        self.assertTrue(user.username)

    def test_login_by_email_and_by_username(self):
        user = User.objects.create_user(
            username='demo', email='demo@mail.ru', password='Montazh2026'
        )
        self.assertTrue(self.client.login(username='demo@mail.ru', password='Montazh2026'))
        self.client.logout()
        self.assertTrue(self.client.login(username='demo', password='Montazh2026'))
        self.assertEqual(user.avatar_letter, 'D')

    def test_profile_requires_login(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response['Location'])

    def test_profile_update(self):
        User.objects.create_user(username='demo', email='d@m.ru', password='Montazh2026')
        self.client.login(username='demo', password='Montazh2026')
        response = self.client.post(reverse('profile'), {
            'action': 'profile',
            'store_name': 'Двери и Интерьер',
            'manager_full_name': 'Петров П. П.',
            'phone': '+7 (900) 000-00-00',
            'email': 'new@mail.ru',
            'city': 'г. Москва',
            'street': 'ул. Ленина',
            'house': '10',
        })
        self.assertRedirects(response, reverse('profile'))
        user = User.objects.get(username='demo')
        self.assertEqual(user.store_name, 'Двери и Интерьер')
        self.assertEqual(user.email, 'new@mail.ru')
