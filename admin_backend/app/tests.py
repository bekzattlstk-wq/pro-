import tempfile

from django.contrib import admin as django_admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from .models import Notification, Order


class BackendTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls._media_dir = tempfile.TemporaryDirectory()
        cls._media_settings = override_settings(MEDIA_ROOT=cls._media_dir.name)
        cls._media_settings.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls._media_settings.disable()
        cls._media_dir.cleanup()

    def setUp(self):
        user_model = get_user_model()
        self.admin = user_model.objects.create_superuser("admin", "admin@example.com", "pass-123456")
        self.manager = user_model.objects.create_user("manager", password="pass-123456")
        self.other = user_model.objects.create_user("other", password="pass-123456")
        self.manager.groups.add(Group.objects.get_or_create(name="Managers")[0])
        self.other.groups.add(Group.objects.get_or_create(name="Installers")[0])
        self.client = APIClient()
        self.order = Order.objects.create(
            shop_name="Академия дверей", service_name="Монтаж дверей",
            customer_name="Иван Иванов", customer_phone="+79999999999",
            price="20000.00", manager=self.manager,
        )

    def authenticate(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def test_order_number_and_notification(self):
        self.assertTrue(self.order.number.startswith("АД"))
        self.assertEqual(
            Notification.objects.filter(order=self.order, manager=self.manager).count(), 1
        )
        self.order.status = Order.Status.PAUSED
        self.order.save()
        self.assertEqual(
            Notification.objects.filter(order=self.order, manager=self.manager).count(), 2
        )

    def test_manager_sees_only_own_orders(self):
        self.authenticate(self.manager)
        response = self.client.get("/api/orders/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(self.client.post("/api/orders/", {}, format="json").status_code, 400)
        self.authenticate(self.other)
        self.assertEqual(self.client.get(f"/api/orders/{self.order.pk}/").status_code, 404)

    def test_admin_can_create_order(self):
        self.authenticate(self.admin)
        response = self.client.post("/api/orders/", {
            "shop_name": "Магазин", "service_name": "Установка",
            "customer_name": "Петр Петров", "customer_phone": "+79998887766",
            "price": "1000.00", "manager": self.other.pk,
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["number"].startswith("АД"))

    def test_file_requires_admin_and_creates_notification(self):
        self.authenticate(self.manager)
        self.assertEqual(self.client.post("/api/order-files/", {
            "order": self.order.pk,
            "file": SimpleUploadedFile("test.txt", b"hello"),
        }).status_code, 403)
        self.authenticate(self.admin)
        response = self.client.post("/api/order-files/", {
            "order": self.order.pk,
            "file": SimpleUploadedFile("test.txt", b"hello"),
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            Notification.objects.filter(order=self.order, manager=self.manager).count(), 2
        )
        self.authenticate(self.other)
        self.assertEqual(self.client.get(f"/api/order-files/{response.data['id']}/download/").status_code, 404)

    def test_token_login_and_logout(self):
        response = self.client.post("/api/token/", {
            "username": "manager", "password": "pass-123456",
        }, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.data)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {response.data['token']}")
        self.assertEqual(self.client.get("/api/me/").status_code, 200)
        self.assertEqual(self.client.post("/api/logout/").status_code, 204)
        self.assertEqual(self.client.get("/api/me/").status_code, 401)

    def test_notifications_belong_to_manager(self):
        notification = Notification.objects.get(order=self.order, manager=self.manager)
        self.authenticate(self.other)
        self.assertEqual(self.client.get("/api/notifications/").data["count"], 0)
        self.assertEqual(
            self.client.post(f"/api/notifications/{notification.pk}/mark-read/").status_code,
            404,
        )
        self.authenticate(self.manager)
        self.assertEqual(
            self.client.post(f"/api/notifications/{notification.pk}/mark-read/").status_code,
            200,
        )
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    def test_manager_marks_all_notifications_as_read(self):
        Notification.objects.create(manager=self.manager, order=self.order, message="Второе уведомление")
        Notification.objects.create(manager=self.other, order=self.order, message="Другой пользователь")
        self.authenticate(self.manager)
        response = self.client.post("/api/notifications/mark-all-read/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["updated"], 2)
        self.assertFalse(Notification.objects.filter(manager=self.manager, is_read=False).exists())
        self.assertTrue(Notification.objects.filter(manager=self.other, is_read=False).exists())

    def test_password_change_revokes_token(self):
        self.authenticate(self.manager)
        response = self.client.post("/api/me/password/", {
            "old_password": "pass-123456",
            "new_password": "changed-pass-123456",
        }, format="json")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.client.get("/api/me/").status_code, 401)
        self.assertTrue(get_user_model().objects.get(pk=self.manager.pk).check_password("changed-pass-123456"))

    def test_admin_page_available_to_staff(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get("/admin/app/order/").status_code, 200)
        self.client.logout()
        self.client.force_login(self.manager)
        self.assertEqual(self.client.get("/admin/app/order/").status_code, 302)

    def test_admin_api_requires_staff(self):
        self.authenticate(self.manager)
        self.assertEqual(self.client.get("/api/admin/orders/").status_code, 403)
        self.authenticate(self.admin)
        self.assertEqual(self.client.get("/api/admin/orders/").status_code, 200)

    def test_admin_dashboard(self):
        self.authenticate(self.admin)
        response = self.client.get("/api/admin/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("counts", response.data)
        self.assertIn("orders", response.data)

    def test_admin_changes_status_and_adds_comment(self):
        self.authenticate(self.admin)
        response = self.client.patch(
            f"/api/admin/orders/{self.order.pk}/",
            {"status": Order.Status.WAITING_CALL},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.order.status_history.count(), 1)

        response = self.client.post(
            f"/api/admin/orders/{self.order.pk}/comment/",
            {"text": "Дата согласована"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.order.comments.count(), 1)

    def test_user_creates_order_and_uploads_shop_file(self):
        self.authenticate(self.other)
        response = self.client.post("/api/orders/", {
            "shop_name": "Магазин",
            "service_name": "Монтаж",
            "customer_name": "Клиент",
            "customer_phone": "+996700000000",
            "price": "1000.00",
        }, format="json")
        self.assertEqual(response.status_code, 201)
        order = Order.objects.get(pk=response.data["id"])
        self.assertEqual(order.created_by, self.other)

        response = self.client.post("/api/order-files/", {
            "order": order.pk,
            "file": SimpleUploadedFile("shop.txt", b"hello"),
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["source"], "shop")

    def test_admin_delete_is_soft(self):
        self.authenticate(self.admin)
        response = self.client.delete(f"/api/admin/orders/{self.order.pk}/")
        self.assertEqual(response.status_code, 204)
        self.order.refresh_from_db()
        self.assertTrue(self.order.is_deleted)

    def test_admin_panel_delete_is_soft(self):
        order_admin = django_admin.site._registry[Order]
        request = type("Request", (), {"user": self.admin})()
        order_admin.delete_model(request, self.order)
        self.order.refresh_from_db()
        self.assertTrue(self.order.is_deleted)
        self.assertEqual(self.order.deleted_by, self.admin)

    def test_admin_panel_rejects_invalid_status_transition(self):
        from .admin import OrderAdminForm

        form = OrderAdminForm(
            data={
                "shop_name": self.order.shop_name,
                "service_name": self.order.service_name,
                "customer_name": self.order.customer_name,
                "customer_phone": self.order.customer_phone,
                "price": str(self.order.price),
                "status": Order.Status.COMPLETED,
                "manager": self.manager.pk,
                "created_by": "",
                "installer": "",
                "work_at": "",
                "planned_date": "",
                "is_urgent": "",
                "is_deleted": "",
                "deleted_at": "",
                "deleted_by": "",
            },
            instance=self.order,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("status", form.errors)
