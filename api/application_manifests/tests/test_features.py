# api/application_manifests/tests/conftest.py
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authorized_client(api_client):
    User = get_user_model()
    user = User.objects.create(email="test@example.com", first_name="Test", last_name="User", type="EXPORTER")
    api_client.force_authenticate(user=user)
    return api_client
