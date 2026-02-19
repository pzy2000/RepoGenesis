import os
import pytest


def pytest_configure():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api_crud.settings")


@pytest.fixture
def api_client(db):
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def user_data():
    return {
        "username": "alice",
        "password": "StrongPassw0rd!",
        "password2": "StrongPassw0rd!",
        "email": "alice@example.com",
        "first_name": "Alice",
        "last_name": "Tester",
    }


@pytest.fixture
def create_user(db):
    from django.contrib.auth.models import User

    def _create(username: str, password: str):
        user = User.objects.create_user(username=username, password=password, email=f"{username}@example.com")
        return user

    return _create



