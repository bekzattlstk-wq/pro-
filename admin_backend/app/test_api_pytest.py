import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_token_login_returns_token():
    user = get_user_model().objects.create_user(
        username="pytest_user", password="test-pass-123456"
    )
    response = APIClient().post(
        "/api/token/",
        {"username": user.username, "password": "test-pass-123456"},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["token"]
